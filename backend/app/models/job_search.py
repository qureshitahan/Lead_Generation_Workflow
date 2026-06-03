"""Tracks in-app job discovery searches (Bright Data, Apify, etc.)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class JobSearch(Base, TimestampMixin):
    __tablename__ = "job_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    provider: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    keyword: Mapped[str] = mapped_column(String(512), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    filters: Mapped[Optional[dict]] = mapped_column(JSON)

    # External run id (Bright Data snapshot_id).
    snapshot_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    import_batch_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    status: Mapped[str] = mapped_column(String(30), index=True, default="pending", nullable=False)
    records_fetched: Mapped[Optional[int]] = mapped_column(Integer)
    records_imported: Mapped[Optional[int]] = mapped_column(Integer)
    records_duplicates: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    requested_by: Mapped[Optional[str]] = mapped_column(String(255))
