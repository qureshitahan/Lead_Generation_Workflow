"""Apify LinkedIn jobs adapter (placeholder mapping for the second source).

Apify actors use camelCase-ish field names. Adjust aliases when you test a real
Apify dataset; the structure mirrors the Bright Data adapter.
"""
from __future__ import annotations

from app.models.enums import JobSource
from app.services.ingestion.base import JobSourceAdapter, register_adapter


@register_adapter
class ApifyAdapter(JobSourceAdapter):
    source_key = JobSource.APIFY

    field_map = {
        "title": ["title", "jobTitle"],
        "company_name": ["companyName", "company"],
        "company_id": ["companyId"],
        "location": ["location", "jobLocation"],
        "description": ["description", "descriptionText", "jobDescription"],
        "source_url": ["jobUrl", "url", "link"],
        "company_linkedin_url": ["companyUrl", "companyLinkedinUrl"],
        "employment_type": ["employmentType", "contractType"],
        "seniority": ["seniorityLevel", "experienceLevel"],
        "job_function": ["jobFunction", "function"],
        "industries": ["industries", "industry"],
        "salary_text": ["salary", "salaryInfo"],
        "job_poster": ["posterFullName", "jobPoster"],
        "applicants_count": ["applicantsCount", "applicants"],
        "easy_apply": ["easyApply"],
        "posted_at": ["postedAt", "publishedAt", "postedTime"],
    }

    id_keys = ["id", "jobId", "jobPostingId"]
    url_keys = ["jobUrl", "url", "link"]
