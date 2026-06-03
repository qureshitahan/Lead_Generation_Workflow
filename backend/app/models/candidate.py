"""Candidate profiles the recruiting company can pitch to jobs."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Structured parse output.
    target_roles: Mapped[Optional[list]] = mapped_column(JSON)        # ["ML Engineer", ...]
    skills: Mapped[Optional[list]] = mapped_column(JSON)              # ["Python", "PyTorch", ...]
    years_experience: Mapped[Optional[float]] = mapped_column(Float)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    work_authorization: Mapped[Optional[str]] = mapped_column(String(255))
    availability: Mapped[Optional[str]] = mapped_column(String(255))
    expected_salary: Mapped[Optional[str]] = mapped_column(String(255))

    # Raw + summarized resume content.
    resume_text: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    selling_points: Mapped[Optional[list]] = mapped_column(JSON)      # short bullet strengths

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    matches = relationship("Match", back_populates="candidate")
