"""Company enrichment layer (Milestone 3).

Pluggable providers behind a common interface. The active provider is chosen by
ENRICHMENT_PROVIDER. Until real API keys exist, the `stub` provider returns
deterministic mock data so the rest of the pipeline can be built and tested.
"""
from app.core.config import settings
from app.services.enrichment.apollo import ApolloEnrichmentProvider
from app.services.enrichment.base import EnrichmentProvider, EnrichmentResult
from app.services.enrichment.stub import StubEnrichmentProvider
from app.services.enrichment.zoominfo import ZoomInfoEnrichmentProvider

_PROVIDERS = {
    "stub": StubEnrichmentProvider,
    "apollo": ApolloEnrichmentProvider,
    "zoominfo": ZoomInfoEnrichmentProvider,
}


def get_enrichment_provider() -> EnrichmentProvider:
    """Return the configured enrichment provider (defaults to stub)."""
    provider_cls = _PROVIDERS.get(settings.enrichment_provider, StubEnrichmentProvider)
    return provider_cls()


__all__ = [
    "EnrichmentProvider",
    "EnrichmentResult",
    "get_enrichment_provider",
]
