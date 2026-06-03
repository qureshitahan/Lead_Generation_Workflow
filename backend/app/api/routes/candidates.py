"""Candidate creation (with resume parsing) and listing endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.candidate import Candidate
from app.schemas.entities import CandidateOut, Page
from app.schemas.requests import CandidateCreateRequest
from app.services.candidates import parse_resume

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("", response_model=Page[CandidateOut])
def list_candidates(
    db: Session = Depends(get_db),
    active_only: bool = True,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Candidate)
    count_query = select(func.count()).select_from(Candidate)
    if active_only:
        query = query.where(Candidate.is_active.is_(True))
        count_query = count_query.where(Candidate.is_active.is_(True))
    query = query.order_by(Candidate.created_at.desc()).limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    total = db.execute(count_query).scalar_one()
    return Page[CandidateOut](items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=CandidateOut, status_code=201)
def create_candidate(payload: CandidateCreateRequest, db: Session = Depends(get_db)):
    """Create a candidate. Fields not provided are parsed from resume_text."""
    parsed = parse_resume(payload.resume_text or "")

    candidate = Candidate(
        name=payload.name,
        resume_text=payload.resume_text,
        target_roles=payload.target_roles or parsed.target_roles or None,
        skills=payload.skills or parsed.skills or None,
        years_experience=(
            payload.years_experience
            if payload.years_experience is not None
            else parsed.years_experience
        ),
        location=payload.location or parsed.location,
        work_authorization=payload.work_authorization,
        availability=payload.availability,
        expected_salary=payload.expected_salary,
        summary=payload.summary or parsed.summary,
        selling_points=payload.selling_points or parsed.selling_points or None,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.delete("/{candidate_id}", status_code=204)
def deactivate_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.is_active = False
    db.commit()
