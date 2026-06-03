"""Candidate-to-job match scores with explanation and a generated pitch."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Float, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Match(Base, TimestampMixin):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True, nullable=False)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), index=True, nullable=False)

    score: Mapped[float] = mapped_column(Float, nullable=False)        # 0-100
    matched_skills: Mapped[Optional[list]] = mapped_column(JSON)
    missing_skills: Mapped[Optional[list]] = mapped_column(JSON)
    concerns: Mapped[Optional[list]] = mapped_column(JSON)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    pitch: Mapped[Optional[str]] = mapped_column(Text)                 # short pitch summary

    job = relationship("Job", back_populates="matches")
    candidate = relationship("Candidate", back_populates="matches")
