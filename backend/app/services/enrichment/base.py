"""Enrichment provider interface and result shape."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EnrichmentContact:
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    email_status: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    confidence_score: Optional[float] = None
    # Provider-side stable id (e.g. Apollo person id) used to reveal email/phone.
    external_id: Optional[str] = None
    # Company domain this contact belongs to (helps re-match during reveal).
    domain: Optional[str] = None


@dataclass
class EnrichmentResult:
    found: bool
    source: str
    domain: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    headquarters: Optional[str] = None
    phone: Optional[str] = None
    funding: Optional[str] = None
    revenue: Optional[str] = None
    contacts: Optional[List[EnrichmentContact]] = None


class EnrichmentProvider(ABC):
    """Implement this to add a new enrichment data source."""

    name: str = "base"

    @abstractmethod
    def enrich_company(
        self,
        company_name: str,
        *,
        linkedin_url: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> EnrichmentResult:
        """Look up firmographics for a company."""

    @abstractmethod
    def find_contacts(
        self,
        company_name: str,
        *,
        domain: Optional[str] = None,
        target_titles: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[EnrichmentContact]:
        """Find candidate contacts at the company."""

    def reveal_contacts(self, contacts: List[EnrichmentContact]) -> None:
        """Reveal email/phone for the given contacts, mutating them in place.

        Default is a no-op (providers that already return contact details, or that
        cannot reveal more, simply do nothing). Providers like Apollo override this
        to call a paid enrichment endpoint for the selected contacts only.
        """
        return None
