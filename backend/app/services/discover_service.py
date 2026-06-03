"""Orchestrates job discovery + import into the existing pipeline."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import AuditAction, JobSearchStatus
from app.models.job_search import JobSearch
from app.services.audit import log_action
from app.services.discovery import JobSearchParams, get_discovery_provider
from app.services.discovery.brightdata import BrightDataDiscoveryError
from app.services.import_service import ImportResult, import_parsed_jobs
from app.services.ingestion import get_adapter

# Register discovery provider implementations on import.
from app.services.discovery import brightdata as _bd  # noqa: F401
from app.services.discovery import stub as _stub  # noqa: F401


@dataclass
class DiscoverImportResult:
    """Combined discovery + import outcome."""

    search_id: int
    provider: str
    snapshot_id: Optional[str]
    records_fetched: int
    import_result: ImportResult


def discover_and_import_jobs(
    db: Session,
    params: JobSearchParams,
    *,
    provider_name: Optional[str] = None,
    target_roles: Optional[List[str]] = None,
    requested_by: Optional[str] = "recruiter",
) -> DiscoverImportResult:
    """Run provider discovery, then ingest via the standard import pipeline."""
    provider = get_discovery_provider(provider_name)
    batch_id = uuid.uuid4().hex[:12]

    search = JobSearch(
        provider=provider.name,
        keyword=params.keyword,
        location=params.location or None,
        filters=params.to_filters_dict(),
        import_batch_id=batch_id,
        status=JobSearchStatus.RUNNING,
        requested_by=requested_by,
    )
    db.add(search)
    db.commit()
    db.refresh(search)

    try:
        raw_records, meta = provider.discover(params)
        search.snapshot_id = meta.snapshot_id
        search.records_fetched = meta.records_fetched
        db.flush()

        adapter = get_adapter(provider.source_key)
        parsed = adapter.parse_records(raw_records)
        import_result = import_parsed_jobs(
            db,
            source=provider.source_key,
            parsed=parsed,
            target_roles=target_roles or settings.target_roles,
            batch_id=batch_id,
        )

        search.status = JobSearchStatus.IMPORTED
        search.records_imported = import_result.imported
        search.records_duplicates = import_result.duplicates

        log_action(
            db,
            AuditAction.JOB_DISCOVER,
            entity_type="job_search",
            entity_id=search.id,
            actor=requested_by or "recruiter",
            summary=(
                f"Discovered {meta.records_fetched} job(s) via {provider.name}; "
                f"imported {import_result.imported} new"
            ),
            detail={
                "keyword": params.keyword,
                "location": params.location,
                "snapshot_id": meta.snapshot_id,
                "batch_id": batch_id,
                "imported": import_result.imported,
                "duplicates": import_result.duplicates,
            },
            commit=True,
        )
        db.commit()
        db.refresh(search)

        return DiscoverImportResult(
            search_id=search.id,
            provider=provider.name,
            snapshot_id=meta.snapshot_id,
            records_fetched=meta.records_fetched,
            import_result=import_result,
        )
    except Exception as exc:
        search.status = JobSearchStatus.FAILED
        search.error_message = str(exc)[:2000]
        db.commit()
        if isinstance(exc, BrightDataDiscoveryError):
            raise
        raise BrightDataDiscoveryError(str(exc)) from exc
