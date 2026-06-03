"""Field-level normalization helpers and the dedup fingerprint.

Pure functions (no DB access) so they are easy to unit-test and reuse.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Optional

from app.models.enums import EmploymentType


def clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_company_name(name: Any) -> str:
    """Lowercase, strip punctuation and common suffixes for dedup/matching."""
    text = (clean_text(name) or "").lower()
    text = re.sub(r"[\.,]", "", text)
    # Drop trailing legal suffixes that cause false mismatches.
    text = re.sub(r"\b(inc|llc|ltd|corp|co|gmbh|plc|limited|incorporated)\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_employment_type(value: Any) -> Optional[str]:
    text = (clean_text(value) or "").lower()
    if not text:
        return None
    if "full" in text:
        return EmploymentType.FULL_TIME
    if "part" in text:
        return EmploymentType.PART_TIME
    if "contract" in text or "contractor" in text:
        return EmploymentType.CONTRACT
    if "temp" in text:
        return EmploymentType.TEMPORARY
    if "intern" in text:
        return EmploymentType.INTERNSHIP
    return EmploymentType.OTHER


def parse_posted_at(value: Any) -> Optional[datetime]:
    """Best-effort date parsing across common LinkedIn/export formats."""
    text = clean_text(value)
    if not text:
        return None
    # Try a set of explicit formats first.
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    # Handle ISO 8601 with timezone offset.
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def parse_int(value: Any) -> Optional[int]:
    text = clean_text(value)
    if not text:
        return None
    digits = re.sub(r"[^0-9]", "", text)
    return int(digits) if digits else None


def parse_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    text = (clean_text(value) or "").lower()
    if text in ("true", "yes", "1"):
        return True
    if text in ("false", "no", "0"):
        return False
    return None


def build_dedup_key(
    source_job_id: Optional[str],
    company_name: Optional[str],
    title: Optional[str],
    location: Optional[str],
    source_url: Optional[str],
) -> str:
    """Stable fingerprint for deduplication.

    Prefers the source posting id. Falls back to a hash of
    company + title + location + url when the id is missing.
    """
    if source_job_id:
        basis = f"id:{source_job_id.strip().lower()}"
    else:
        basis = "|".join(
            [
                normalize_company_name(company_name),
                (clean_text(title) or "").lower(),
                (clean_text(location) or "").lower(),
                (clean_text(source_url) or "").lower(),
            ]
        )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()
