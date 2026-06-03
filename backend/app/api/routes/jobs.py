"""Job listing, detail, and human review (approve/reject) endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import AuditAction, JobStatus
from app.models.job import Job
from app.schemas.entities import JobOut, Page
from app.schemas.requests import JobReviewRequest
from app.services.audit import log_action

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=Page[JobOut])
def list_jobs(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    source: Optional[str] = None,
    min_relevance: Optional[float] = None,
    direct_employer: Optional[bool] = None,
    search: Optional[str] = None,
    sort: str = Query("relevance", pattern="^(relevance|posted|created|match)$"),
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Job)
    count_query = select(func.count()).select_from(Job)

    filters = []
    if status:
        filters.append(Job.status == status)
    if source:
        filters.append(Job.source == source)
    if min_relevance is not None:
        filters.append(Job.relevance_score >= min_relevance)
    if direct_employer is not None:
        filters.append(Job.is_direct_employer.is_(direct_employer))
    if search:
        like = f"%{search}%"
        filters.append((Job.title.ilike(like)) | (Job.company_name.ilike(like)))

    for f in filters:
        query = query.where(f)
        count_query = count_query.where(f)

    sort_map = {
        "relevance": Job.relevance_score.desc(),
        "posted": Job.posted_at.desc(),
        "created": Job.created_at.desc(),
        "match": Job.best_match_score.desc(),
    }
    query = query.order_by(sort_map[sort]).limit(limit).offset(offset)

    items = db.execute(query).scalars().all()
    total = db.execute(count_query).scalar_one()
    return Page[JobOut](items=items, total=total, limit=limit, offset=offset)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/review", response_model=JobOut)
def review_job(job_id: int, payload: JobReviewRequest, db: Session = Depends(get_db)):
    """Human approves or rejects a job for pursuit."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if payload.status not in (JobStatus.APPROVED, JobStatus.REJECTED):
        raise HTTPException(
            status_code=400, detail="status must be 'approved' or 'rejected'"
        )

    job.status = payload.status
    job.reviewed_by = payload.reviewed_by
    job.reviewed_at = datetime.utcnow()
    job.review_notes = payload.notes

    log_action(
        db,
        AuditAction.JOB_APPROVAL,
        entity_type="job",
        entity_id=job.id,
        actor=payload.reviewed_by or "recruiter",
        summary=f"Job {payload.status} by {payload.reviewed_by}",
        detail={"notes": payload.notes},
    )
    db.commit()
    db.refresh(job)
    return job
