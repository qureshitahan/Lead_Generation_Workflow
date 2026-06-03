"""In-app job discovery (Bright Data / future providers)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.job_search import JobSearch
from app.schemas.entities import DiscoverImportSummary, JobSearchOut, Page
from app.schemas.requests import JobDiscoverRequest
from app.services.discovery.base import JobSearchParams
from app.services.discovery.brightdata import BrightDataDiscoveryError
from app.services.discover_service import discover_and_import_jobs

router = APIRouter(prefix="/discover", tags=["discover"])


@router.post("/jobs", response_model=DiscoverImportSummary)
def discover_jobs(payload: JobDiscoverRequest, db: Session = Depends(get_db)):
    """Search LinkedIn jobs via Bright Data (or stub) and import into the pipeline.

    This call may take 30s–several minutes while Bright Data collects results.
    """
    params = JobSearchParams(
        keyword=payload.keyword,
        location=payload.location,
        time_range=payload.time_range,
        country=payload.country,
        job_type=payload.job_type,
        experience_level=payload.experience_level,
        remote=payload.remote,
        company=payload.company,
        location_radius=payload.location_radius,
        limit=payload.limit,
    )
    try:
        outcome = discover_and_import_jobs(
            db,
            params,
            provider_name=payload.provider,
            requested_by=payload.requested_by,
        )
    except BrightDataDiscoveryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    imp = outcome.import_result
    return DiscoverImportSummary(
        search_id=outcome.search_id,
        provider=outcome.provider,
        snapshot_id=outcome.snapshot_id,
        records_fetched=outcome.records_fetched,
        source=imp.source,
        batch_id=imp.batch_id,
        total_records=imp.total_records,
        imported=imp.imported,
        duplicates=imp.duplicates,
        errors=imp.errors,
        job_ids=imp.job_ids,
        error_messages=imp.error_messages,
    )


@router.get("/searches", response_model=Page[JobSearchOut])
def list_searches(
    db: Session = Depends(get_db),
    limit: int = Query(20, le=100),
    offset: int = 0,
):
    """Recent discovery searches for the dashboard history panel."""
    query = select(JobSearch).order_by(JobSearch.created_at.desc()).limit(limit).offset(offset)
    count_q = select(func.count()).select_from(JobSearch)
    items = db.execute(query).scalars().all()
    total = db.execute(count_q).scalar_one()
    return Page[JobSearchOut](items=items, total=total, limit=limit, offset=offset)


@router.get("/searches/{search_id}", response_model=JobSearchOut)
def get_search(search_id: int, db: Session = Depends(get_db)):
    row = db.get(JobSearch, search_id)
    if not row:
        raise HTTPException(status_code=404, detail="Search not found")
    return row
