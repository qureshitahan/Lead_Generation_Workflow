"""Job discovery providers — fetch jobs from external APIs (not file uploads).

Discovery is separate from file-parsing adapters:
  * **Discovery** = call Bright Data / Apify API with search criteria → raw JSON records
  * **Ingestion adapter** = map those records to canonical fields → existing import pipeline

Set JOB_DISCOVERY_PROVIDER in `.env` (brightdata | stub | apify future).
"""
from app.services.discovery.base import (
    DiscoveryMeta,
    JobDiscoveryProvider,
    JobSearchParams,
    get_discovery_provider,
)
from app.services.discovery.brightdata import BrightDataDiscoveryProvider
from app.services.discovery.stub import StubDiscoveryProvider

__all__ = [
    "DiscoveryMeta",
    "JobDiscoveryProvider",
    "JobSearchParams",
    "get_discovery_provider",
    "BrightDataDiscoveryProvider",
    "StubDiscoveryProvider",
]
