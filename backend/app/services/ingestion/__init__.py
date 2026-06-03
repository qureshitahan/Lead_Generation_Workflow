"""Modular job ingestion layer.

Each job data source (Bright Data, Apify, manual upload, ...) implements a
`JobSourceAdapter` that knows how to parse that source's CSV/JSON into a list of
`ParsedJob` objects with a canonical field mapping. The raw payload is always
preserved. New sources are added by writing one adapter and registering it.
"""
from app.services.ingestion.base import (
    ParsedJob,
    JobSourceAdapter,
    get_adapter,
    register_adapter,
)
from app.services.ingestion.apify import ApifyAdapter
from app.services.ingestion.brightdata import BrightDataAdapter
from app.services.ingestion.manual import ManualAdapter

__all__ = [
    "ParsedJob",
    "JobSourceAdapter",
    "get_adapter",
    "register_adapter",
    "ApifyAdapter",
    "BrightDataAdapter",
    "ManualAdapter",
]
