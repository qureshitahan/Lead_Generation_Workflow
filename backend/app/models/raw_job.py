"""Raw, unmodified job records exactly as received from a source.

We never discard the original payload. This table is the source of truth for
debugging, re-normalization, and comparing source quality (Bright Data vs Apify).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RawJob(Base, TimestampMixin):
    __tablename__ = "raw_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Which source produced this record (brightdata, apify, manual).
    source: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    # Optional identifier of the import batch/run this record came from.
    import_batch_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    # The complete original record as a JSON blob. Nothing is dropped here.
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # The source's own job posting id, pulled out for convenience/dedup.
    source_job_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text)

    # Set once this raw record has been turned into a normalized Job.
    processed: Mapped[bool] = mapped_column(default=False, nullable=False)
    processing_error: Mapped[Optional[str]] = mapped_column(Text)

    job = relationship("Job", back_populates="raw_job", uselist=False)
