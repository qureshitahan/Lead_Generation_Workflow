"""One-off script: real Bright Data discover + import + report."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal, init_db
from app.models.job import Job
from app.services.discovery.base import JobSearchParams
from app.services.discovery.brightdata import BrightDataDiscoveryError
from app.services.discover_service import discover_and_import_jobs


def main() -> None:
    print("=== Bright Data E2E test ===")
    print(f"Provider: {settings.job_discovery_provider}")
    print(f"Dataset ID: {settings.brightdata_dataset_id}")
    print(f"API key set: {bool(settings.brightdata_api_key)}")

    if not settings.brightdata_api_key:
        print("ERROR: BRIGHTDATA_API_KEY missing")
        sys.exit(1)

    init_db()
    db = SessionLocal()

    params = JobSearchParams(
        keyword="Machine Learning Engineer",
        location="United States",
        time_range="Past week",
        limit=25,
    )
    print(f"\nSearch: keyword={params.keyword!r} location={params.location!r} time_range={params.time_range!r} limit={params.limit}")

    try:
        outcome = discover_and_import_jobs(db, params, provider_name="brightdata")
    except BrightDataDiscoveryError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
    finally:
        pass

    imp = outcome.import_result
    print("\n--- Discovery + import summary ---")
    print(f"Search ID:      {outcome.search_id}")
    print(f"Snapshot ID:    {outcome.snapshot_id}")
    print(f"Records fetched: {outcome.records_fetched}")
    print(f"Batch ID:       {imp.batch_id}")
    print(f"Total parsed:   {imp.total_records}")
    print(f"Imported (new): {imp.imported}")
    print(f"Duplicates:     {imp.duplicates}")
    print(f"Errors:         {imp.errors}")
    if imp.error_messages:
        print("Error messages:")
        for msg in imp.error_messages:
            print(f"  - {msg}")

    # Show jobs from this batch
    jobs = db.execute(
        select(Job).where(Job.source == "brightdata").order_by(Job.created_at.desc()).limit(30)
    ).scalars().all()

    batch_jobs = [j for j in jobs if j.raw_job_id]  # recent
    print(f"\n--- Recent jobs in DB (up to 30, source=brightdata) ---")
    for j in jobs[: imp.imported + imp.duplicates + 5]:
        direct = "DIRECT" if j.is_direct_employer else ("STAFFING" if j.is_staffing_or_recruiting else "?")
        print(
            f"  [{direct}] rel={j.relevance_score or 0:>5.0f} | {j.title[:50]} @ {j.company_name} | "
            f"role={j.matched_role or '-'} | status={j.status}"
        )
        if j.relevance_reason:
            print(f"       relevance: {j.relevance_reason[:120]}")
        if j.employer_explanation:
            print(f"       employer:  {j.employer_explanation[:120]}")

    db.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
