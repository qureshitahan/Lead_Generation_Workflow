"""Email draft generation, editing, approval, and (gated) sending."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.candidate import Candidate
from app.models.company import Company
from app.models.contact import Contact
from app.models.email_draft import EmailDraft
from app.models.enums import AuditAction, EmailStatus
from app.models.job import Job
from app.models.match import Match
from app.models.suppression import OutreachHistory
from app.schemas.entities import EmailDraftOut, Page
from app.schemas.requests import (
    EmailGenerateRequest,
    EmailStatusRequest,
    EmailUpdateRequest,
)
from app.services.audit import log_action
from app.services.email_generation import generate_email
from app.services.email_providers import get_email_provider

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("", response_model=Page[EmailDraftOut])
def list_emails(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(EmailDraft)
    count_query = select(func.count()).select_from(EmailDraft)
    if status:
        query = query.where(EmailDraft.status == status)
        count_query = count_query.where(EmailDraft.status == status)
    query = query.order_by(EmailDraft.created_at.desc()).limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    total = db.execute(count_query).scalar_one()
    return Page[EmailDraftOut](items=items, total=total, limit=limit, offset=offset)


@router.post("/generate", response_model=EmailDraftOut, status_code=201)
def generate_draft(payload: EmailGenerateRequest, db: Session = Depends(get_db)):
    job = db.get(Job, payload.job_id)
    candidate = db.get(Candidate, payload.candidate_id)
    if not job or not candidate:
        raise HTTPException(status_code=404, detail="Job or candidate not found")

    contact = db.get(Contact, payload.contact_id) if payload.contact_id else None
    match = db.get(Match, payload.match_id) if payload.match_id else None
    company = db.get(Company, job.company_id) if job.company_id else None

    content = generate_email(job, company, contact, candidate, match)
    draft = EmailDraft(
        job_id=job.id,
        company_id=job.company_id,
        contact_id=contact.id if contact else None,
        candidate_id=candidate.id,
        match_id=match.id if match else None,
        subject=content.subject,
        body=content.body,
        status=EmailStatus.DRAFT,
    )
    db.add(draft)
    log_action(
        db,
        AuditAction.EMAIL_DRAFT,
        entity_type="email_draft",
        summary=f"Drafted email for job {job.id} / candidate {candidate.id}",
    )
    db.commit()
    db.refresh(draft)
    return draft


@router.patch("/{draft_id}", response_model=EmailDraftOut)
def update_draft(draft_id: int, payload: EmailUpdateRequest, db: Session = Depends(get_db)):
    draft = db.get(EmailDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status == EmailStatus.SENT:
        raise HTTPException(status_code=400, detail="Cannot edit a sent email")
    if payload.subject is not None:
        draft.subject = payload.subject
    if payload.body is not None:
        draft.body = payload.body
    db.commit()
    db.refresh(draft)
    return draft


@router.post("/{draft_id}/status", response_model=EmailDraftOut)
def set_status(draft_id: int, payload: EmailStatusRequest, db: Session = Depends(get_db)):
    """Update draft status (approve, mark replied/bounced/not_interested, etc.)."""
    draft = db.get(EmailDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft.status = payload.status
    if payload.status == EmailStatus.APPROVED:
        draft.approved_by = payload.approved_by
        draft.approved_at = datetime.utcnow()
    log_action(
        db,
        AuditAction.EMAIL_APPROVAL,
        entity_type="email_draft",
        entity_id=draft.id,
        actor=payload.approved_by or "recruiter",
        summary=f"Email status -> {payload.status}",
    )
    db.commit()
    db.refresh(draft)
    return draft


@router.post("/{draft_id}/send", response_model=EmailDraftOut)
def send_email(draft_id: int, db: Session = Depends(get_db)):
    """Send an APPROVED draft via the configured provider.

    Requires explicit prior approval (human-in-the-loop). The default stub
    provider does not actually transmit anything.
    """
    draft = db.get(EmailDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != EmailStatus.APPROVED:
        raise HTTPException(
            status_code=400, detail="Email must be APPROVED before sending"
        )

    contact = db.get(Contact, draft.contact_id) if draft.contact_id else None
    if not contact or not contact.email:
        raise HTTPException(status_code=400, detail="No contact email to send to")
    if contact.do_not_contact:
        raise HTTPException(status_code=400, detail="Contact is on do-not-contact list")

    provider = get_email_provider()
    result = provider.send(
        to_email=contact.email,
        subject=draft.subject,
        body=draft.body,
        from_email=settings.outreach_from_email,
        from_name=settings.outreach_from_name,
    )
    if not result.sent:
        raise HTTPException(status_code=502, detail=result.error or "Send failed")

    draft.status = EmailStatus.SENT
    draft.provider = result.provider
    draft.provider_message_id = result.message_id
    draft.sent_at = datetime.utcnow()
    db.add(
        OutreachHistory(
            company_id=draft.company_id,
            contact_id=draft.contact_id,
            channel="email",
            detail=f"Sent via {result.provider}",
        )
    )
    log_action(
        db,
        AuditAction.EMAIL_SEND,
        entity_type="email_draft",
        entity_id=draft.id,
        summary=f"Sent via {result.provider} ({result.message_id})",
    )
    db.commit()
    db.refresh(draft)
    return draft
