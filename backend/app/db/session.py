"""Database engine, session factory, and FastAPI dependency."""
from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# SQLite needs a special flag for multi-threaded FastAPI use.
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Ensure the directory for the SQLite file exists.
    db_path = settings.database_url.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. For MVP we use create_all; swap to Alembic later."""
    # Import models so they register on the metadata before create_all.
    from app import models  # noqa: F401

    Base = models.Base
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()


# Minimal additive migrations for SQLite (create_all won't add columns to
# pre-existing tables). Each entry: table -> {column: column DDL type}.
_ADDITIVE_COLUMNS = {
    "contacts": {
        "email_status": "VARCHAR(30)",
        "external_id": "VARCHAR(64)",
        "phone_reveal_status": "VARCHAR(20)",
    },
}


def _apply_lightweight_migrations() -> None:
    """Add any missing columns to existing tables (idempotent, SQLite-safe)."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _ADDITIVE_COLUMNS.items():
            if table not in existing_tables:
                continue
            present = {col["name"] for col in inspector.get_columns(table)}
            for column, ddl_type in columns.items():
                if column not in present:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {ddl_type}'))
