"""Bright Data LinkedIn job adapter.

Maps Bright Data's CSV/JSON columns to canonical fields. Bright Data field names
vary slightly between exports, so each canonical field lists several aliases.
"""
from __future__ import annotations

from app.models.enums import JobSource
from app.services.ingestion.base import JobSourceAdapter, register_adapter


@register_adapter
class BrightDataAdapter(JobSourceAdapter):
    source_key = JobSource.BRIGHTDATA

    field_map = {
        "title": ["job_title", "title"],
        "company_name": ["company_name", "company"],
        "company_id": ["company_id"],
        "location": ["job_location", "location"],
        "description": [
            "job_summary",
            "job_description_formatted",
            "formatted_description",
            "description",
        ],
        "source_url": ["job_url", "url"],
        "company_linkedin_url": ["company_url", "company_linkedin_url"],
        "employment_type": ["job_employment_type", "employment_type"],
        "seniority": ["job_seniority_level", "seniority_level", "seniority"],
        "job_function": ["job_function", "function"],
        "industries": ["job_industries", "industries"],
        "salary_text": ["job_base_pay_range", "salary", "pay_range", "base_salary"],
        "job_poster": ["job_poster", "job_poster_name"],
        "applicants_count": ["job_num_applicants", "applicants_count", "num_applicants"],
        "easy_apply": ["job_easy_apply", "easy_apply"],
        "posted_at": ["job_posted_date", "job_posted_time", "posted_date", "posted_time"],
    }

    id_keys = ["job_posting_id", "job_posting_id_str", "jobPostingId", "id"]
    url_keys = ["job_url", "url"]
