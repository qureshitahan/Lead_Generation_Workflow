"""Job discovery provider interface and search parameters."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.config import settings


@dataclass
class JobSearchParams:
    """Recruiter-facing search criteria (provider-agnostic)."""

    keyword: str
    location: str = ""
    time_range: str = ""          # e.g. "Past week", "Past month"
    country: str = ""
    job_type: str = ""            # e.g. "Full-time"
    experience_level: str = ""
    remote: str = ""              # On-site | Remote | Hybrid
    company: str = ""
    location_radius: str = ""
    limit: Optional[int] = None   # max jobs to fetch; provider default if None

    def to_filters_dict(self) -> Dict[str, Any]:
        """Persist optional filters without provider-specific field names."""
        return {
            k: v
            for k, v in {
                "time_range": self.time_range,
                "country": self.country,
                "job_type": self.job_type,
                "experience_level": self.experience_level,
                "remote": self.remote,
                "company": self.company,
                "location_radius": self.location_radius,
                "limit": self.limit,
            }.items()
            if v not in (None, "")
        }


@dataclass
class DiscoveryMeta:
    """Metadata returned alongside raw records from a discovery run."""

    provider: str
    snapshot_id: Optional[str] = None
    records_fetched: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


class JobDiscoveryProvider(ABC):
    """Fetch job listings from an external source using search criteria."""

    name: str = "base"
    #: Source key used when storing RawJob / Job rows (matches ingestion adapter).
    source_key: str = "base"

    @abstractmethod
    def discover(self, params: JobSearchParams) -> tuple[List[dict], DiscoveryMeta]:
        """Run a search and return (raw_records, metadata)."""


_PROVIDERS: Dict[str, type[JobDiscoveryProvider]] = {}


def register_discovery_provider(cls: type[JobDiscoveryProvider]) -> type[JobDiscoveryProvider]:
    _PROVIDERS[cls.name] = cls
    return cls


def get_discovery_provider(provider_name: Optional[str] = None) -> JobDiscoveryProvider:
    name = (provider_name or settings.job_discovery_provider).lower()
    if name not in _PROVIDERS:
        raise ValueError(
            f"Unknown job discovery provider '{name}'. "
            f"Registered: {sorted(_PROVIDERS)}"
        )
    return _PROVIDERS[name]()
