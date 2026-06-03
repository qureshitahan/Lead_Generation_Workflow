"""Normalized job records: the clean internal representation of a posting.

A Job is derived from exactly one RawJob, optionally linked to a Company, and
carries the relevance + direct-employer classification results plus the human
approval status that gates the rest of the workflow.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import JobStatus


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    raw_job_id: Mapped[Optional[int]] = mapped_column(ForeignKey("raw_jobs.id"))
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), index=True)

    source: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    # Dedup key: the source's posting id when present.
    source_job_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    # Fallback dedup fingerprint (company+title+location+url hash).
    dedup_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # --- Normalized core fields ---
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    company_linkedin_url: Mapped[Optional[str]] = mapped_column(String(512))

    employment_type: Mapped[Optional[str]] = mapped_column(String(30))
    seniority: Mapped[Optional[str]] = mapped_column(String(100))
    job_function: Mapped[Optional[str]] = mapped_column(String(255))
    industries: Mapped[Optional[str]] = mapped_column(String(512))
    salary_text: Mapped[Optional[str]] = mapped_column(String(255))
    job_poster: Mapped[Optional[str]] = mapped_column(String(255))
    applicants_count: Mapped[Optional[int]] = mapped_column(Integer)
    easy_apply: Mapped[Optional[bool]] = mapped_column(Boolean)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # --- Relevance classification ---
    relevance_score: Mapped[Optional[float]] = mapped_column(Float)
    relevance_reason: Mapped[Optional[str]] = mapped_column(Text)
    matched_role: Mapped[Optional[str]] = mapped_column(String(255))

    # --- Direct employer classification (per-job; company holds the rollup) ---
    is_direct_employer: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_staffing_or_recruiting: Mapped[Optional[bool]] = mapped_column(Boolean)
    employer_confidence: Mapped[Optional[float]] = mapped_column(Float)
    employer_explanation: Mapped[Optional[str]] = mapped_column(Text)

    # --- Best candidate match score (denormalized for dashboard speed) ---
    best_match_score: Mapped[Optional[float]] = mapped_column(Float)

    # --- Workflow ---
    status: Mapped[str] = mapped_column(
        String(30), default=JobStatus.NEW, index=True, nullable=False
    )
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    review_notes: Mapped[Optional[str]] = mapped_column(Text)

    raw_job = relationship("RawJob", back_populates="job")
    company = relationship("Company", back_populates="jobs")
    matches = relationship("Match", back_populates="job")
