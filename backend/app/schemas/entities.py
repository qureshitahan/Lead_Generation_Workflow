"""Read/response schemas mirroring the ORM models.

All use `from_attributes=True` so they can be built directly from ORM objects.
"""
from __future__ import annotations

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int


class JobOut(ORMModel):
    id: int
    source: str
    source_job_id: Optional[str] = None
    title: str
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    employment_type: Optional[str] = None
    seniority: Optional[str] = None
    job_function: Optional[str] = None
    industries: Optional[str] = None
    salary_text: Optional[str] = None
    job_poster: Optional[str] = None
    applicants_count: Optional[int] = None
    easy_apply: Optional[bool] = None
    posted_at: Optional[datetime] = None
    relevance_score: Optional[float] = None
    relevance_reason: Optional[str] = None
    matched_role: Optional[str] = None
    is_direct_employer: Optional[bool] = None
    is_staffing_or_recruiting: Optional[bool] = None
    employer_confidence: Optional[float] = None
    employer_explanation: Optional[str] = None
    best_match_score: Optional[float] = None
    status: str
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: datetime


class CompanyOut(ORMModel):
    id: int
    name: str
    domain: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    headquarters: Optional[str] = None
    phone: Optional[str] = None
    funding: Optional[str] = None
    revenue: Optional[str] = None
    is_direct_employer: Optional[bool] = None
    is_staffing_or_recruiting: Optional[bool] = None
    employer_confidence: Optional[float] = None
    employer_explanation: Optional[str] = None
    enrichment_status: str
    enrichment_source: Optional[str] = None
    do_not_contact: bool
    created_at: datetime


class ContactOut(ORMModel):
    id: int
    company_id: int
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    email_status: Optional[str] = None
    phone: Optional[str] = None
    phone_reveal_status: Optional[str] = None
    linkedin_url: Optional[str] = None
    source: Optional[str] = None
    confidence_score: Optional[float] = None
    usefulness_score: Optional[float] = None
    rank_reason: Optional[str] = None
    approved_for_outreach: bool
    do_not_contact: bool
    created_at: datetime


class CandidateOut(ORMModel):
    id: int
    name: str
    target_roles: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    years_experience: Optional[float] = None
    location: Optional[str] = None
    work_authorization: Optional[str] = None
    availability: Optional[str] = None
    expected_salary: Optional[str] = None
    resume_text: Optional[str] = None
    summary: Optional[str] = None
    selling_points: Optional[List[str]] = None
    is_active: bool
    created_at: datetime


class MatchOut(ORMModel):
    id: int
    job_id: int
    candidate_id: int
    score: float
    matched_skills: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    concerns: Optional[List[str]] = None
    reason: Optional[str] = None
    pitch: Optional[str] = None
    created_at: datetime


class EmailDraftOut(ORMModel):
    id: int
    job_id: Optional[int] = None
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    candidate_id: Optional[int] = None
    match_id: Optional[int] = None
    subject: str
    body: str
    status: str
    provider: Optional[str] = None
    provider_message_id: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime


class CallOut(ORMModel):
    id: int
    job_id: Optional[int] = None
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    candidate_id: Optional[int] = None
    match_id: Optional[int] = None
    phone_number: Optional[str] = None
    script: Optional[str] = None
    status: str
    transcript: Optional[str] = None
    outcome_notes: Optional[str] = None
    human_handoff_needed: bool
    meeting_requested: bool
    created_at: datetime


class AuditLogOut(ORMModel):
    id: int
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    actor: str
    summary: Optional[str] = None
    detail: Optional[dict] = None
    created_at: datetime


class JobSearchOut(ORMModel):
    id: int
    provider: str
    keyword: str
    location: Optional[str] = None
    filters: Optional[dict] = None
    snapshot_id: Optional[str] = None
    import_batch_id: Optional[str] = None
    status: str
    records_fetched: Optional[int] = None
    records_imported: Optional[int] = None
    records_duplicates: Optional[int] = None
    error_message: Optional[str] = None
    requested_by: Optional[str] = None
    created_at: datetime


class DiscoverImportSummary(BaseModel):
    """Result of an in-app job search + import."""

    search_id: int
    provider: str
    snapshot_id: Optional[str] = None
    records_fetched: int
    source: str
    batch_id: str
    total_records: int
    imported: int
    duplicates: int
    errors: int
    job_ids: List[int]
    error_messages: List[str]


class ImportSummary(BaseModel):
    source: str
    batch_id: str
    total_records: int
    imported: int
    duplicates: int
    errors: int
    job_ids: List[int]
    error_messages: List[str]


class DashboardStats(BaseModel):
    jobs_total: int
    jobs_by_status: dict
    companies_total: int
    direct_employers: int
    staffing_firms: int
    contacts_total: int
    candidates_total: int
    matches_total: int
    email_drafts_total: int
    calls_total: int
