"""Base classes and registry for job source adapters."""
from __future__ import annotations

import csv
import io
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


# Canonical field names produced by every adapter. The normalization service
# consumes these keys regardless of which source they came from.
CANONICAL_FIELDS = [
    "title",
    "company_name",
    "company_id",
    "location",
    "description",
    "source_url",
    "company_linkedin_url",
    "employment_type",
    "seniority",
    "job_function",
    "industries",
    "salary_text",
    "job_poster",
    "applicants_count",
    "easy_apply",
    "posted_at",
]


@dataclass
class ParsedJob:
    """One job parsed from a source file.

    `raw_payload` is the complete original record (never dropped). `fields` holds
    canonical keys mapped from the source-specific field names.
    """

    raw_payload: Dict[str, Any]
    fields: Dict[str, Any] = field(default_factory=dict)
    source_job_id: Optional[str] = None
    source_url: Optional[str] = None


class JobSourceAdapter(ABC):
    """Interface every job source must implement."""

    #: Source key stored on records (e.g. "brightdata").
    source_key: str = "base"

    #: Maps canonical field name -> list of possible source column/key names.
    field_map: Dict[str, List[str]] = {}

    #: Source keys that hold the posting id (checked in order).
    id_keys: List[str] = []

    #: Source keys that hold the job url (checked in order).
    url_keys: List[str] = []

    def parse(self, content: bytes | str, content_type: Optional[str] = None) -> List[ParsedJob]:
        """Parse raw file content (CSV or JSON) into ParsedJob records."""
        records = self._load_records(content, content_type)
        return self.parse_records(records)

    def parse_records(self, records: List[dict]) -> List[ParsedJob]:
        """Convert API/JSON records into ParsedJob objects (shared by file + discovery)."""
        return [self._to_parsed(rec) for rec in records]

    # --- helpers ---

    def _load_records(self, content: bytes | str, content_type: Optional[str]) -> List[dict]:
        text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
        text = text.strip()
        if not text:
            return []
        looks_json = (content_type and "json" in content_type) or text[0] in "[{"
        if looks_json:
            return self._load_json(text)
        return self._load_csv(text)

    @staticmethod
    def _load_json(text: str) -> List[dict]:
        data = json.loads(text)
        if isinstance(data, dict):
            # Some exports wrap records under a key like {"data": [...]}.
            for key in ("data", "results", "items", "jobs"):
                if isinstance(data.get(key), list):
                    return data[key]
            return [data]
        return list(data)

    @staticmethod
    def _load_csv(text: str) -> List[dict]:
        reader = csv.DictReader(io.StringIO(text))
        return [dict(row) for row in reader]

    def _to_parsed(self, record: dict) -> ParsedJob:
        fields: Dict[str, Any] = {}
        for canonical, source_keys in self.field_map.items():
            value = self._first_present(record, source_keys)
            if value is not None:
                fields[canonical] = value
        return ParsedJob(
            raw_payload=record,
            fields=fields,
            source_job_id=self._stringify(self._first_present(record, self.id_keys)),
            source_url=self._stringify(self._first_present(record, self.url_keys))
            or self._stringify(fields.get("source_url")),
        )

    @staticmethod
    def _first_present(record: dict, keys: List[str]) -> Any:
        for key in keys:
            if key in record and record[key] not in (None, ""):
                return record[key]
        return None

    @staticmethod
    def _stringify(value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value).strip() or None


# --- Adapter registry -------------------------------------------------------

_REGISTRY: Dict[str, JobSourceAdapter] = {}


def register_adapter(adapter_cls: Type[JobSourceAdapter]) -> Type[JobSourceAdapter]:
    """Class decorator / function to register a source adapter."""
    _REGISTRY[adapter_cls.source_key] = adapter_cls()
    return adapter_cls


def get_adapter(source_key: str) -> JobSourceAdapter:
    if source_key not in _REGISTRY:
        raise ValueError(
            f"Unknown job source '{source_key}'. Registered: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[source_key]
