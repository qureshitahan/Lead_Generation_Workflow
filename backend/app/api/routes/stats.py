"""Dashboard stats + recent audit log."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.call import Call
from app.models.candidate import Candidate
from app.models.company import Company
from app.models.contact import Contact
from app.models.email_draft import EmailDraft
from app.models.job import Job
from app.models.match import Match
from app.schemas.entities import AuditLogOut, DashboardStats

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    def count(model, *where):
        q = select(func.count()).select_from(model)
        for w in where:
            q = q.where(w)
        return db.execute(q).scalar_one()

    status_rows = db.execute(
        select(Job.status, func.count()).group_by(Job.status)
    ).all()
    jobs_by_status = {status: cnt for status, cnt in status_rows}

    return DashboardStats(
        jobs_total=count(Job),
        jobs_by_status=jobs_by_status,
        companies_total=count(Company),
        direct_employers=count(Company, Company.is_direct_employer.is_(True)),
        staffing_firms=count(Company, Company.is_staffing_or_recruiting.is_(True)),
        contacts_total=count(Contact),
        candidates_total=count(Candidate),
        matches_total=count(Match),
        email_drafts_total=count(EmailDraft),
        calls_total=count(Call),
    )


@router.get("/audit", response_model=list[AuditLogOut])
def recent_audit(db: Session = Depends(get_db), limit: int = Query(50, le=200)):
    rows = db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    ).scalars().all()
    return rows
