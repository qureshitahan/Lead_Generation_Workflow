"""Application configuration.

All settings load from environment variables (see `.env.example`). The app is
designed to run fully on stub/mock providers, so every integration key is
optional. Real keys can be added incrementally as milestones progress.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Core ---
    app_name: str = "Lead Generation Workflow"
    environment: str = "development"
    database_url: str = "sqlite:///./data/leadgen.db"
    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # --- Target roles (relevance scoring defaults) ---
    target_roles: List[str] = [
        "Software Engineer",
        "AI Engineer",
        "Machine Learning Engineer",
        "Data Engineer",
    ]

    # --- Job discovery (in-app search) ---
    # Provider: brightdata | stub (stub uses sample_data; apify later)
    job_discovery_provider: str = "brightdata"
    brightdata_api_key: str = ""
    brightdata_dataset_id: str = "gd_lpfll7v5hcqtkxl6l"
    brightdata_poll_interval_seconds: int = 5
    brightdata_poll_timeout_seconds: int = 300
    brightdata_default_limit_per_search: int = 50

    # --- Job sources (file import adapters) ---
    apify_api_token: str = ""

    # --- Enrichment ---
    enrichment_provider: str = "stub"
    apollo_api_key: str = ""
    zoominfo_api_key: str = ""

    # --- Email ---
    email_provider: str = "stub"
    postmark_server_token: str = ""
    sendgrid_api_key: str = ""
    outreach_from_email: str = "outreach@example.com"
    outreach_from_name: str = "Your Recruiting Team"

    # --- Voice ---
    voice_provider: str = "stub"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    elevenlabs_api_key: str = ""

    # --- LLM ---
    llm_provider: str = "none"
    openai_api_key: str = ""

    # --- Safety / compliance ---
    max_outreach_per_company: int = 3
    outreach_cooldown_days: int = 14

    @field_validator("cors_origins", "target_roles", mode="before")
    @classmethod
    def _split_csv(cls, value):
        """Allow comma-separated strings from env vars to become lists."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
