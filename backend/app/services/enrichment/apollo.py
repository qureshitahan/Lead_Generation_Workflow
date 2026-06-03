"""Apollo.io enrichment provider (skeleton).

Wire up real API calls here once APOLLO_API_KEY is set. The HTTP scaffolding is
in place; for now it falls back to the stub so the pipeline keeps working.
"""
from __future__ import annotations

from typing import List, Optional

from app.core.config import settings
from app.services.enrichment.base import (
    EnrichmentContact,
    EnrichmentProvider,
    EnrichmentResult,
)
from app.services.enrichment.stub import StubEnrichmentProvider

APOLLO_BASE_URL = "https://api.apollo.io/v1"


class ApolloEnrichmentProvider(EnrichmentProvider):
    name = "apollo"

    def __init__(self) -> None:
        self.api_key = settings.apollo_api_key
        self._fallback = StubEnrichmentProvider()

    def enrich_company(self, company_name: str, *, linkedin_url: Optional[str] = None) -> EnrichmentResult:
        if not self.api_key:
            # No key yet: behave like the stub but tag the source clearly.
            result = self._fallback.enrich_company(company_name, linkedin_url=linkedin_url)
            result.source = "apollo (stub fallback: no API key)"
            return result
        # TODO: POST {APOLLO_BASE_URL}/organizations/enrich with the domain/name.
        # Parse the response into EnrichmentResult(found=True, source="apollo", ...).
        raise NotImplementedError("Apollo enrich_company not yet implemented")

    def find_contacts(
        self,
        company_name: str,
        *,
        domain: Optional[str] = None,
        target_titles: Optional[List[str]] = None,
    ) -> List[EnrichmentContact]:
        if not self.api_key:
            return self._fallback.find_contacts(
                company_name, domain=domain, target_titles=target_titles
            )
        # TODO: POST {APOLLO_BASE_URL}/mixed_people/search filtered by titles + domain.
        raise NotImplementedError("Apollo find_contacts not yet implemented")
