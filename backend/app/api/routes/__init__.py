"""API route registration."""
from fastapi import APIRouter

from app.api.routes import (
    calls,
    candidates,
    companies,
    contacts,
    discover,
    emails,
    imports,
    jobs,
    matches,
    stats,
    webhooks,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(stats.router)
api_router.include_router(imports.router)
api_router.include_router(discover.router)
api_router.include_router(jobs.router)
api_router.include_router(companies.router)
api_router.include_router(contacts.router)
api_router.include_router(candidates.router)
api_router.include_router(matches.router)
api_router.include_router(emails.router)
api_router.include_router(calls.router)
api_router.include_router(webhooks.router)

__all__ = ["api_router"]
