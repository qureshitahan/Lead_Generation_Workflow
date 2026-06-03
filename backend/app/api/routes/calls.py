"""Call queue: script generation, approval, status updates (no auto-dialing)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.call import Call
from app.models.candidate import Candidate
from app.models.company import Company
from app.models.contact import Contact
from app.models.enums import AuditAction, CallStatus
from app.models.job import Job
from app.models.match import Match
from app.schemas.entities import CallOut, Page
from app.schemas.requests import CallGenerateRequest, CallStatusRequest
from app.services.audit import log_action
from app.services.voice import generate_call_script

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("", response_model=Page[CallOut])
def list_calls(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Call)
    count_query = select(func.count()).select_from(Call)
    if status:
        query = query.where(Call.status == status)
        count_query = count_query.where(Call.status == status)
    query = query.order_by(Call.created_at.desc()).limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    total = db.execute(count_query).scalar_one()
    return Page[CallOut](items=items, total=total, limit=limit, offset=offset)


@router.post("/generate", response_model=CallOut, status_code=201)
def generate_call(payload: CallGenerateRequest, db: Session = Depends(get_db)):
    """Generate a call script and queue the call (status=queued, unapproved)."""
    job = db.get(Job, payload.job_id)
    candidate = db.get(Candidate, payload.candidate_id)
    if not job or not candidate:
        raise HTTPException(status_code=404, detail="Job or candidate not found")

    contact = db.get(Contact, payload.contact_id) if payload.contact_id else None
    match = db.get(Match, payload.match_id) if payload.match_id else None
    company = db.get(Company, job.company_id) if job.company_id else None

    script = generate_call_script(job, company, contact, candidate, match)
    call = Call(
        job_id=job.id,
        company_id=job.company_id,
        contact_id=contact.id if contact else None,
        candidate_id=candidate.id,
        match_id=match.id if match else None,
        phone_number=(contact.phone if contact else None) or (company.phone if company else None),
        script=script,
        status=CallStatus.QUEUED,
    )
    db.add(call)
    log_action(
        db,
        AuditAction.CALL_SCRIPT,
        entity_type="call",
        summary=f"Generated call script for job {job.id}",
    )
    db.commit()
    db.refresh(call)
    return call


@router.post("/{call_id}/status", response_model=CallOut)
def update_call_status(call_id: int, payload: CallStatusRequest, db: Session = Depends(get_db)):
    """Approve a call or record its outcome (interested, handoff, meeting, etc.)."""
    call = db.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    call.status = payload.status
    if payload.transcript is not None:
        call.transcript = payload.transcript
    if payload.outcome_notes is not None:
        call.outcome_notes = payload.outcome_notes
    if payload.human_handoff_needed is not None:
        call.human_handoff_needed = payload.human_handoff_needed
    if payload.meeting_requested is not None:
        call.meeting_requested = payload.meeting_requested
    if payload.status == CallStatus.APPROVED:
        call.approved_by = payload.approved_by
        call.approved_at = datetime.utcnow()

    action = (
        AuditAction.CALL_APPROVAL
        if payload.status == CallStatus.APPROVED
        else AuditAction.CALL_PLACED
    )
    log_action(
        db,
        action,
        entity_type="call",
        entity_id=call.id,
        actor=payload.approved_by or "recruiter",
        summary=f"Call status -> {payload.status}",
    )
    db.commit()
    db.refresh(call)
    return call
