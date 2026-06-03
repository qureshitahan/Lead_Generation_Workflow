"""Model package: import all models so SQLAlchemy registers them on Base."""
from app.db.base import Base
from app.models.audit import AuditLog
from app.models.call import Call
from app.models.candidate import Candidate
from app.models.company import Company
from app.models.contact import Contact
from app.models.email_draft import EmailDraft
from app.models.job import Job
from app.models.match import Match
from app.models.raw_job import RawJob
from app.models.suppression import OutreachHistory, Suppression

__all__ = [
    "Base",
    "AuditLog",
    "Call",
    "Candidate",
    "Company",
    "Contact",
    "EmailDraft",
    "Job",
    "Match",
    "RawJob",
    "OutreachHistory",
    "Suppression",
]
