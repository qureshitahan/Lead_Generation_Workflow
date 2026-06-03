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
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    confidence_score: Optional[float] = None


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
    def enrich_company(self, company_name: str, *, linkedin_url: Optional[str] = None) -> EnrichmentResult:
        """Look up firmographics for a company."""

    @abstractmethod
    def find_contacts(
        self, company_name: str, *, domain: Optional[str] = None, target_titles: Optional[List[str]] = None
    ) -> List[EnrichmentContact]:
        """Find candidate contacts at the company."""
