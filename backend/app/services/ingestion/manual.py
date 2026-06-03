"""Manual upload adapter.

Accepts already-canonical field names, so a user can paste/upload a simple
CSV/JSON with columns like title, company_name, location, description, source_url.
"""
from __future__ import annotations

from app.models.enums import JobSource
from app.services.ingestion.base import CANONICAL_FIELDS, JobSourceAdapter, register_adapter


@register_adapter
class ManualAdapter(JobSourceAdapter):
    source_key = JobSource.MANUAL

    # Canonical name maps to itself (plus a couple friendly aliases).
    field_map = {name: [name] for name in CANONICAL_FIELDS}
    field_map["company_name"] = ["company_name", "company"]
    field_map["source_url"] = ["source_url", "url"]

    id_keys = ["job_posting_id", "source_job_id", "id"]
    url_keys = ["source_url", "url"]
