"""Personalized email drafts tied to a job/company/contact/candidate match.

Nothing is sent automatically in the MVP. Drafts must be human-approved.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import EmailStatus


class EmailDraft(Base, TimestampMixin):
    __tablename__ = "email_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    job_id: Mapped[Optional[int]] = mapped_column(ForeignKey("jobs.id"), index=True)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), index=True)
    contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contacts.id"), index=True)
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidates.id"), index=True)
    match_id: Mapped[Optional[int]] = mapped_column(ForeignKey("matches.id"), index=True)

    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(30), default=EmailStatus.DRAFT, index=True, nullable=False
    )
    # Provider used / message id once sent (future milestone).
    provider: Mapped[Optional[str]] = mapped_column(String(50))
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255))

    approved_by: Mapped[Optional[str]] = mapped_column(String(255))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
