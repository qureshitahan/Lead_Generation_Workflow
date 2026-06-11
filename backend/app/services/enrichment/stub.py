"""Stub enrichment provider.

Returns deterministic mock data derived from the company name so the enrichment
and contact-discovery flows can be built and demoed without real API keys.
"""
from __future__ import annotations

import re
from typing import List, Optional

from app.services.enrichment.base import (
    EnrichmentContact,
    EnrichmentProvider,
    EnrichmentResult,
)


def _guess_domain(company_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "", company_name.lower())
    return f"{slug or 'company'}.example.com"


class StubEnrichmentProvider(EnrichmentProvider):
    name = "stub"

    def enrich_company(
        self,
        company_name: str,
        *,
        linkedin_url: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> EnrichmentResult:
        domain = domain or _guess_domain(company_name)
        return EnrichmentResult(
            found=True,
            source=self.name,
            domain=domain,
            website=f"https://{domain}",
            linkedin_url=linkedin_url,
            industry="Software Development",
            employee_count=120,
            headquarters="Remote / Unknown (stub)",
            phone="+1-555-0100",
            funding="Series A (stub)",
            revenue=None,
        )

    def find_contacts(
        self,
        company_name: str,
        *,
        domain: Optional[str] = None,
        target_titles: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[EnrichmentContact]:
        domain = domain or _guess_domain(company_name)
        contacts = [
            EnrichmentContact(
                name="Jordan Recruiter",
                title="Technical Recruiter",
                email=f"jordan.recruiter@{domain}",
                linkedin_url=None,
                confidence_score=70.0,
            ),
            EnrichmentContact(
                name="Alex Engineering",
                title="Director of Engineering",
                email=f"alex.eng@{domain}",
                linkedin_url=None,
                confidence_score=60.0,
            ),
        ]
        if limit is not None:
            return contacts[: max(0, limit)]
        return contacts
