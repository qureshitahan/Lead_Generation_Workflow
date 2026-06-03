"""Stub discovery provider — uses local sample data when no API key is configured."""
from __future__ import annotations

import json
import os
from typing import List

from app.models.enums import JobSource
from app.services.discovery.base import (
    DiscoveryMeta,
    JobDiscoveryProvider,
    JobSearchParams,
    register_discovery_provider,
)

SAMPLE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "sample_data", "brightdata_sample.json"
)


@register_discovery_provider
class StubDiscoveryProvider(JobDiscoveryProvider):
    name = "stub"
    source_key = JobSource.BRIGHTDATA

    def discover(self, params: JobSearchParams) -> tuple[List[dict], DiscoveryMeta]:
        with open(os.path.abspath(SAMPLE_PATH), encoding="utf-8") as f:
            records: List[dict] = json.load(f)

        keyword = params.keyword.lower()
        filtered = [
            r
            for r in records
            if keyword in (r.get("job_title") or "").lower()
            or keyword in (r.get("job_summary") or "").lower()
        ]
        if not filtered:
            filtered = records

        limit = params.limit or len(filtered)
        filtered = filtered[:limit]

        return filtered, DiscoveryMeta(
            provider=self.name,
            snapshot_id="stub-local",
            records_fetched=len(filtered),
            extra={"note": "stub provider — no Bright Data API call"},
        )
