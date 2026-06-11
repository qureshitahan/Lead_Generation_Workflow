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
    # Public HTTPS base URL for inbound webhooks (e.g. ngrok tunnel to port 8000).
    app_public_url: str = ""

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
    apollo_base_url: str = "https://api.apollo.io/api/v1"
    # Max contacts to request per company from Apollo People Search.
    apollo_contacts_per_company: int = 10
    # Reveal real emails/phones via People Enrichment (consumes credits).
    apollo_reveal_contacts: bool = True
    # How many top-ranked contacts per company to reveal emails for (cost control).
    apollo_enrich_contacts_limit: int = 5
    # Also reveal personal emails (in addition to work emails) — extra credits.
    apollo_reveal_personal_emails: bool = False
    # Phone reveal is delivered asynchronously to a webhook; requires a public URL.
    apollo_reveal_phone_number: bool = False
    # Full webhook URL passed to Apollo. If empty, built from APP_PUBLIC_URL + secret.
    apollo_phone_webhook_url: str = ""
    # Shared secret appended as ?token=... on the webhook URL (recommended).
    apollo_phone_webhook_secret: str = ""
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


def resolve_apollo_phone_webhook_url(cfg: Settings | None = None) -> str:
    """Return the HTTPS URL Apollo should POST phone reveals to.

    Priority:
      1. APOLLO_PHONE_WEBHOOK_URL if set explicitly
      2. {APP_PUBLIC_URL}/api/webhooks/apollo/phone[?token=SECRET]
    """
    cfg = cfg or settings
    explicit = (cfg.apollo_phone_webhook_url or "").strip()
    if explicit:
        return explicit

    public = (cfg.app_public_url or "").strip().rstrip("/")
    if not public:
        return ""

    url = f"{public}/api/webhooks/apollo/phone"
    secret = (cfg.apollo_phone_webhook_secret or "").strip()
    if secret:
        url = f"{url}?token={secret}"
    return url
