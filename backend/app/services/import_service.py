"""Import orchestrator: the heart of Milestone 1.

Pipeline for one uploaded file:
  1. Parse with the source adapter (Bright Data / Apify / manual).
  2. Store the raw record verbatim (RawJob).
  3. Normalize fields into the internal Job shape.
  4. Deduplicate by source_job_id, else by fingerprint.
  5. Upsert the Company and run relevance + direct-employer classifiers.
  6. Persist the Job (status = REVIEW) and write audit entries.

Returns a summary so the dashboard can show what happened.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import AuditAction, JobStatus
from app.models.job import Job
from app.models.raw_job import RawJob
from app.services import normalization as norm
from app.services.audit import log_action
from app.services.classification import classify_direct_employer, classify_relevance
from app.services.companies import get_or_create_company
from app.services.ingestion import ParsedJob, get_adapter


@dataclass
class ImportResult:
    source: str
    batch_id: str
    total_records: int = 0
    imported: int = 0
    duplicates: int = 0
    errors: int = 0
    job_ids: List[int] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)


def import_jobs(
    db: Session,
    *,
    source: str,
    content: bytes | str,
    content_type: Optional[str] = None,
    target_roles: Optional[List[str]] = None,
    batch_id: Optional[str] = None,
) -> ImportResult:
    """Import jobs from uploaded/pasted file content."""
    adapter = get_adapter(source)
    parsed = adapter.parse(content, content_type=content_type)
    return import_parsed_jobs(
        db, source=source, parsed=parsed, target_roles=target_roles, batch_id=batch_id
    )


def import_parsed_jobs(
    db: Session,
    *,
    source: str,
    parsed: List[ParsedJob],
    target_roles: Optional[List[str]] = None,
    batch_id: Optional[str] = None,
) -> ImportResult:
    """Run the core ingest pipeline on already-parsed records (file or API discovery)."""
    batch_id = batch_id or uuid.uuid4().hex[:12]
    result = ImportResult(source=source, batch_id=batch_id, total_records=len(parsed))

    for record in parsed:
        try:
            job = _ingest_one(db, source, batch_id, record, target_roles)
            if job is None:
                result.duplicates += 1
            else:
                result.imported += 1
                result.job_ids.append(job.id)
        except Exception as exc:  # keep going; one bad row shouldn't fail the batch
            db.rollback()
            result.errors += 1
            result.error_messages.append(str(exc))

    db.commit()
    log_action(
        db,
        AuditAction.IMPORT,
        entity_type="import_batch",
        summary=(
            f"Imported {result.imported} new, {result.duplicates} duplicate, "
            f"{result.errors} error(s) from {source}"
        ),
        detail={
            "source": source,
            "batch_id": batch_id,
            "total": result.total_records,
            "imported": result.imported,
            "duplicates": result.duplicates,
            "errors": result.errors,
        },
        commit=True,
    )
    return result


def _ingest_one(
    db: Session,
    source: str,
    batch_id: str,
    record: ParsedJob,
    target_roles: Optional[List[str]],
) -> Optional[Job]:
    """Process a single parsed record. Returns the Job, or None if duplicate."""
    fields = record.fields

    title = norm.clean_text(fields.get("title"))
    company_name = norm.clean_text(fields.get("company_name"))
    location = norm.clean_text(fields.get("location"))
    source_url = record.source_url or norm.clean_text(fields.get("source_url"))

    dedup_key = norm.build_dedup_key(
        record.source_job_id, company_name, title, location, source_url
    )

    # --- Dedup check (across all sources) ---
    existing = db.execute(
        select(Job).where(Job.dedup_key == dedup_key)
    ).scalar_one_or_none()
    if existing is None and record.source_job_id:
        existing = db.execute(
            select(Job).where(
                Job.source == source, Job.source_job_id == record.source_job_id
            )
        ).scalar_one_or_none()
    if existing is not None:
        return None

    # --- Always store the raw record ---
    raw = RawJob(
        source=source,
        import_batch_id=batch_id,
        payload=record.raw_payload,
        source_job_id=record.source_job_id,
        source_url=source_url,
        processed=True,
    )
    db.add(raw)
    db.flush()

    # --- Company upsert ---
    company = get_or_create_company(
        db, company_name, linkedin_url=norm.clean_text(fields.get("company_linkedin_url"))
    )

    description = norm.clean_text(fields.get("description"))
    job_poster = norm.clean_text(fields.get("job_poster"))

    # --- Classification ---
    relevance = classify_relevance(title, description, target_roles)
    employer = classify_direct_employer(
        company_name,
        description,
        industry=norm.clean_text(fields.get("industries")),
        job_poster_title=job_poster,
    )

    job = Job(
        raw_job_id=raw.id,
        company_id=company.id if company else None,
        source=source,
        source_job_id=record.source_job_id,
        dedup_key=dedup_key,
        title=title or "(untitled)",
        company_name=company_name,
        location=location,
        description=description,
        source_url=source_url,
        company_linkedin_url=norm.clean_text(fields.get("company_linkedin_url")),
        employment_type=norm.normalize_employment_type(fields.get("employment_type")),
        seniority=norm.clean_text(fields.get("seniority")),
        job_function=norm.clean_text(fields.get("job_function")),
        industries=norm.clean_text(fields.get("industries")),
        salary_text=norm.clean_text(fields.get("salary_text")),
        job_poster=job_poster,
        applicants_count=norm.parse_int(fields.get("applicants_count")),
        easy_apply=norm.parse_bool(fields.get("easy_apply")),
        posted_at=norm.parse_posted_at(fields.get("posted_at")),
        relevance_score=relevance.score,
        relevance_reason=relevance.reason,
        matched_role=relevance.matched_role,
        is_direct_employer=employer.is_direct_employer,
        is_staffing_or_recruiting=employer.is_staffing_or_recruiting,
        employer_confidence=employer.confidence,
        employer_explanation=employer.explanation,
        status=JobStatus.REVIEW,
    )
    db.add(job)
    db.flush()

    # Roll the per-job employer classification up to the company.
    if company and company.is_direct_employer is None:
        company.is_direct_employer = employer.is_direct_employer
        company.is_staffing_or_recruiting = employer.is_staffing_or_recruiting
        company.employer_confidence = employer.confidence
        company.employer_explanation = employer.explanation

    log_action(
        db,
        AuditAction.CLASSIFY_RELEVANCE,
        entity_type="job",
        entity_id=job.id,
        summary=relevance.reason,
        detail={"score": relevance.score, "matched_role": relevance.matched_role},
    )
    log_action(
        db,
        AuditAction.CLASSIFY_EMPLOYER,
        entity_type="job",
        entity_id=job.id,
        summary=employer.explanation,
        detail={
            "is_direct_employer": employer.is_direct_employer,
            "is_staffing_or_recruiting": employer.is_staffing_or_recruiting,
            "confidence": employer.confidence,
        },
    )
    return job
