"""Job listing, detail, and human review (approve/reject) endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import Company
from app.models.contact import Contact
from app.models.enums import AuditAction, JobStatus
from app.models.job import Job
from app.models.raw_job import RawJob
from app.schemas.entities import ContactOut, JobOut, Page
from app.schemas.requests import JobFindContactsRequest, JobReviewRequest
from app.services.audit import log_action
from app.services.companies import get_or_create_company
from app.services.contacts import enrich_and_find_contacts

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _company_for_job(db: Session, job: Job) -> Company:
    """Return the Job's company, creating/linking one if it's missing."""
    if job.company_id:
        company = db.get(Company, job.company_id)
        if company:
            return company
    company = get_or_create_company(
        db, job.company_name, linkedin_url=job.company_linkedin_url
    )
    if company is None:
        raise HTTPException(
            status_code=400,
            detail="This job has no company name, so contacts can't be found.",
        )
    if job.company_id != company.id:
        job.company_id = company.id
        db.flush()
    return company


@router.get("", response_model=Page[JobOut])
def list_jobs(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    source: Optional[str] = None,
    min_relevance: Optional[float] = None,
    direct_employer: Optional[bool] = None,
    search: Optional[str] = None,
    batch_id: Optional[str] = None,
    sort: str = Query("relevance", pattern="^(relevance|posted|created|match)$"),
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Job)
    count_query = select(func.count()).select_from(Job)

    # Filter to a single discovery/import batch (jobs link to RawJob.import_batch_id).
    if batch_id:
        query = query.join(RawJob, Job.raw_job_id == RawJob.id)
        count_query = count_query.join(RawJob, Job.raw_job_id == RawJob.id)

    filters = []
    if batch_id:
        filters.append(RawJob.import_batch_id == batch_id)
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


@router.get("/{job_id}/contacts", response_model=Page[ContactOut])
def list_job_contacts(
    job_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(25, le=25),
):
    """Contacts discovered for the company behind this job (ranked, capped)."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.company_id:
        return Page[ContactOut](items=[], total=0, limit=limit, offset=0)
    query = (
        select(Contact)
        .where(Contact.company_id == job.company_id)
        .order_by(Contact.usefulness_score.desc())
        .limit(limit)
    )
    items = db.execute(query).scalars().all()
    total = (
        db.execute(
            select(func.count())
            .select_from(Contact)
            .where(Contact.company_id == job.company_id)
        ).scalar_one()
    )
    return Page[ContactOut](items=items, total=total, limit=limit, offset=0)


@router.post("/{job_id}/find-contacts", response_model=Page[ContactOut])
def find_job_contacts(
    job_id: int,
    payload: JobFindContactsRequest,
    db: Session = Depends(get_db),
):
    """Enrich the job's company via Apollo and reveal the top-N contacts.

    Returns the full ranked contact list for the company (existing + newly found),
    so the job page can show everything in one place.
    """
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    max_contacts = max(1, min(payload.max_contacts, 25))
    company = _company_for_job(db, job)
    enrich_and_find_contacts(db, company, max_contacts=max_contacts)
    db.commit()

    query = (
        select(Contact)
        .where(Contact.company_id == company.id)
        .order_by(Contact.usefulness_score.desc())
        .limit(max_contacts)
    )
    items = db.execute(query).scalars().all()
    total = (
        db.execute(
            select(func.count())
            .select_from(Contact)
            .where(Contact.company_id == company.id)
        ).scalar_one()
    )
    return Page[ContactOut](items=items, total=total, limit=max_contacts, offset=0)


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
