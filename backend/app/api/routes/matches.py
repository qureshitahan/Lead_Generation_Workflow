"""Candidate-to-job matching endpoints."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.candidate import Candidate
from app.models.enums import AuditAction, JobStatus
from app.models.job import Job
from app.models.match import Match
from app.schemas.entities import MatchOut, Page
from app.schemas.requests import MatchGenerateRequest
from app.services.audit import log_action
from app.services.matching import score_match

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=Page[MatchOut])
def list_matches(
    db: Session = Depends(get_db),
    job_id: Optional[int] = None,
    candidate_id: Optional[int] = None,
    min_score: Optional[float] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Match)
    count_query = select(func.count()).select_from(Match)
    filters = []
    if job_id is not None:
        filters.append(Match.job_id == job_id)
    if candidate_id is not None:
        filters.append(Match.candidate_id == candidate_id)
    if min_score is not None:
        filters.append(Match.score >= min_score)
    for f in filters:
        query = query.where(f)
        count_query = count_query.where(f)
    query = query.order_by(Match.score.desc()).limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    total = db.execute(count_query).scalar_one()
    return Page[MatchOut](items=items, total=total, limit=limit, offset=offset)


@router.post("/generate/{job_id}", response_model=List[MatchOut])
def generate_matches(
    job_id: int, payload: MatchGenerateRequest, db: Session = Depends(get_db)
):
    """Score a job against candidates and upsert Match rows."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cand_query = select(Candidate).where(Candidate.is_active.is_(True))
    if payload.candidate_ids:
        cand_query = cand_query.where(Candidate.id.in_(payload.candidate_ids))
    candidates = db.execute(cand_query).scalars().all()

    results: List[Match] = []
    best_score = job.best_match_score or 0.0
    for candidate in candidates:
        outcome = score_match(job, candidate)
        if outcome.score < payload.min_score:
            continue

        match = db.execute(
            select(Match).where(
                Match.job_id == job.id, Match.candidate_id == candidate.id
            )
        ).scalar_one_or_none()
        if match is None:
            match = Match(job_id=job.id, candidate_id=candidate.id, score=outcome.score)
            db.add(match)
        match.score = outcome.score
        match.matched_skills = outcome.matched_skills
        match.missing_skills = outcome.missing_skills
        match.concerns = outcome.concerns
        match.reason = outcome.reason
        match.pitch = outcome.pitch
        results.append(match)
        best_score = max(best_score, outcome.score)

    job.best_match_score = best_score
    if results and job.status == JobStatus.APPROVED:
        job.status = JobStatus.MATCHED

    log_action(
        db,
        AuditAction.MATCH,
        entity_type="job",
        entity_id=job.id,
        summary=f"Generated {len(results)} match(es); best score {best_score:.0f}.",
        detail={"count": len(results), "best_score": best_score},
    )
    db.commit()
    for m in results:
        db.refresh(m)
    results.sort(key=lambda m: m.score, reverse=True)
    return results
