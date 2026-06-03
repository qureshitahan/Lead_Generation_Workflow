"""Bright Data LinkedIn Jobs — Discover by Keyword API integration.

Flow (async collection):
  1. POST /datasets/v3/trigger  → snapshot_id
  2. GET  /datasets/v3/progress/{snapshot_id} until status == ready
  3. GET  /datasets/v3/snapshot/{snapshot_id}?format=json → job array

Docs: https://docs.brightdata.com/api-reference/scrapers/social-media-apis/linkedin-jobs-discover-by-keyword
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.models.enums import JobSource
from app.services.discovery.base import (
    DiscoveryMeta,
    JobDiscoveryProvider,
    JobSearchParams,
    register_discovery_provider,
)

BRIGHTDATA_API_BASE = "https://api.brightdata.com"
# Default LinkedIn Jobs "discover by keyword" dataset (override via BRIGHTDATA_DATASET_ID).
DEFAULT_LINKEDIN_JOBS_DATASET_ID = "gd_lpfll7v5hcqtkxl6l"


class BrightDataDiscoveryError(Exception):
    """Raised when Bright Data trigger, poll, or download fails."""


@register_discovery_provider
class BrightDataDiscoveryProvider(JobDiscoveryProvider):
    name = "brightdata"
    source_key = JobSource.BRIGHTDATA

    def __init__(self) -> None:
        self.api_key = settings.brightdata_api_key
        self.dataset_id = settings.brightdata_dataset_id or DEFAULT_LINKEDIN_JOBS_DATASET_ID
        self.poll_interval = settings.brightdata_poll_interval_seconds
        self.poll_timeout = settings.brightdata_poll_timeout_seconds

    def discover(self, params: JobSearchParams) -> tuple[List[dict], DiscoveryMeta]:
        if not self.api_key:
            raise BrightDataDiscoveryError(
                "BRIGHTDATA_API_KEY is not set. Add it to backend/.env or set "
                "JOB_DISCOVERY_PROVIDER=stub for local development."
            )

        limit = params.limit or settings.brightdata_default_limit_per_search
        input_row = self._build_input_row(params)
        snapshot_id = self._trigger(input_row, limit)
        self._wait_until_ready(snapshot_id)
        records = self._download_snapshot(snapshot_id)

        return records, DiscoveryMeta(
            provider=self.name,
            snapshot_id=snapshot_id,
            records_fetched=len(records),
            extra={"dataset_id": self.dataset_id, "limit": limit},
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _build_input_row(params: JobSearchParams) -> Dict[str, Any]:
        """Map app search params to Bright Data discover-by-keyword input fields."""
        row: Dict[str, Any] = {
            "keyword": params.keyword.strip(),
            "location": (params.location or "").strip(),
        }
        optional = {
            "country": params.country,
            "time_range": params.time_range,
            "job_type": params.job_type,
            "experience_level": params.experience_level,
            "remote": params.remote,
            "company": params.company,
            "location_radius": params.location_radius,
        }
        for key, value in optional.items():
            if value and str(value).strip():
                row[key] = str(value).strip()
        return row

    def _trigger(self, input_row: Dict[str, Any], limit: int) -> str:
        url = f"{BRIGHTDATA_API_BASE}/datasets/v3/trigger"
        query = {
            "dataset_id": self.dataset_id,
            "type": "discover_new",
            "discover_by": "keyword",
            "include_errors": "true",
            "format": "json",
            "limit_per_input": str(limit),
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                url,
                headers=self._headers(),
                params=query,
                json=[input_row],
            )
        if resp.status_code == 401:
            raise BrightDataDiscoveryError("Bright Data authentication failed (check API key).")
        if resp.status_code >= 400:
            raise BrightDataDiscoveryError(
                f"Bright Data trigger failed ({resp.status_code}): {resp.text[:500]}"
            )
        data = resp.json()
        snapshot_id = data.get("snapshot_id")
        if not snapshot_id:
            raise BrightDataDiscoveryError(
                f"Bright Data trigger returned no snapshot_id: {data}"
            )
        return snapshot_id

    def _wait_until_ready(self, snapshot_id: str) -> None:
        url = f"{BRIGHTDATA_API_BASE}/datasets/v3/progress/{snapshot_id}"
        deadline = time.monotonic() + self.poll_timeout

        with httpx.Client(timeout=30.0) as client:
            while time.monotonic() < deadline:
                resp = client.get(url, headers=self._headers())
                if resp.status_code >= 400:
                    raise BrightDataDiscoveryError(
                        f"Bright Data progress check failed ({resp.status_code}): "
                        f"{resp.text[:300]}"
                    )
                payload = resp.json()
                status = (payload.get("status") or "").lower()
                if status == "ready":
                    return
                if status == "failed":
                    raise BrightDataDiscoveryError(
                        f"Bright Data collection failed for snapshot {snapshot_id}"
                    )
                time.sleep(self.poll_interval)

        raise BrightDataDiscoveryError(
            f"Bright Data search timed out after {self.poll_timeout}s "
            f"(snapshot_id={snapshot_id}). Try again or increase "
            "BRIGHTDATA_POLL_TIMEOUT_SECONDS."
        )

    def _download_snapshot(self, snapshot_id: str) -> List[dict]:
        url = f"{BRIGHTDATA_API_BASE}/datasets/v3/snapshot/{snapshot_id}"
        with httpx.Client(timeout=120.0) as client:
            resp = client.get(
                url,
                headers=self._headers(),
                params={"format": "json"},
            )

        if resp.status_code == 202:
            raise BrightDataDiscoveryError("Snapshot not ready for download (still processing).")
        if resp.status_code >= 400:
            raise BrightDataDiscoveryError(
                f"Bright Data snapshot download failed ({resp.status_code}): "
                f"{resp.text[:300]}"
            )

        data = resp.json()
        return _normalize_snapshot_payload(data)


def _normalize_snapshot_payload(data: Any) -> List[dict]:
    """Bright Data may return a list or a wrapped object — normalize to record list."""
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for key in ("data", "results", "items", "jobs", "records"):
            if isinstance(data.get(key), list):
                return [r for r in data[key] if isinstance(r, dict)]
        if "error" in data:
            raise BrightDataDiscoveryError(str(data.get("error")))
        return [data]
    return []
