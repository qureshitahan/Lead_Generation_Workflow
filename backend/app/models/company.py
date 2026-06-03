"""Company records, including direct-employer classification and enrichment."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import EnrichmentStatus


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    # Normalized key for dedup (lowercased / stripped name).
    normalized_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    # --- Core firmographics (filled by enrichment) ---
    domain: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    website: Mapped[Optional[str]] = mapped_column(String(512))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512))
    industry: Mapped[Optional[str]] = mapped_column(String(255))
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    headquarters: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    funding: Mapped[Optional[str]] = mapped_column(String(255))
    revenue: Mapped[Optional[str]] = mapped_column(String(255))

    # --- Direct employer vs staffing/recruiting classification ---
    is_direct_employer: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_staffing_or_recruiting: Mapped[Optional[bool]] = mapped_column(Boolean)
    employer_confidence: Mapped[Optional[float]] = mapped_column(Float)
    employer_explanation: Mapped[Optional[str]] = mapped_column(Text)

    # --- Enrichment tracking ---
    enrichment_status: Mapped[str] = mapped_column(
        String(30), default=EnrichmentStatus.PENDING, nullable=False
    )
    enrichment_source: Mapped[Optional[str]] = mapped_column(String(50))

    # --- Compliance ---
    do_not_contact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    jobs = relationship("Job", back_populates="company")
    contacts = relationship("Contact", back_populates="company")
