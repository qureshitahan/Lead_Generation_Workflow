"""Contacts discovered at a company, ranked for outreach usefulness."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Contact(Base, TimestampMixin):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512))

    source: Mapped[Optional[str]] = mapped_column(String(50))
    # Confidence that this is a real, reachable, relevant contact (0-100).
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    # How useful this contact type is for our pitch (0-100), drives ranking.
    usefulness_score: Mapped[Optional[float]] = mapped_column(Float)
    rank_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Human gate: a contact must be approved before any outreach.
    approved_for_outreach: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Compliance: per-contact suppression.
    do_not_contact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    company = relationship("Company", back_populates="contacts")
