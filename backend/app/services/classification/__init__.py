"""Job classification services: relevance scoring and direct-employer detection.

Both classifiers are rule-based for the MVP (transparent, fast, no API cost) and
return an explanation alongside the score. The interfaces are designed so an LLM
backend can be swapped in later without changing callers.
"""
from app.services.classification.direct_employer import classify_direct_employer
from app.services.classification.relevance import classify_relevance

__all__ = ["classify_relevance", "classify_direct_employer"]
