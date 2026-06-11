"""Request/input schemas for write endpoints."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class JobReviewRequest(BaseModel):
    """Approve or reject a job (human-in-the-loop gate)."""

    status: str  # "approved" | "rejected"
    reviewed_by: Optional[str] = "recruiter"
    notes: Optional[str] = None


class JobDiscoverRequest(BaseModel):
    """Search for LinkedIn jobs via the configured discovery provider."""

    keyword: str
    location: str = ""
    time_range: str = ""           # Past week | Past month | Any time
    country: str = ""
    job_type: str = ""             # Full-time | Part-time | Contract | ...
    experience_level: str = ""
    remote: str = ""               # On-site | Remote | Hybrid
    company: str = ""
    location_radius: str = ""
    limit: Optional[int] = None
    provider: Optional[str] = None  # override JOB_DISCOVERY_PROVIDER
    requested_by: Optional[str] = "recruiter"


class JobFindContactsRequest(BaseModel):
    """Find + reveal contacts for the company behind a job (Apollo enrichment)."""

    # How many top-ranked contacts to reveal emails/phones for (each costs credits).
    max_contacts: int = 5


class ImportPasteRequest(BaseModel):
    """Import jobs from pasted CSV/JSON text instead of a file upload."""

    source: str = "brightdata"
    content: str
    content_type: Optional[str] = None  # "json" | "csv" (auto-detected if None)


class CandidateCreateRequest(BaseModel):
    name: str
    resume_text: Optional[str] = None
    # Optional explicit overrides; anything omitted is parsed from resume_text.
    target_roles: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    years_experience: Optional[float] = None
    location: Optional[str] = None
    work_authorization: Optional[str] = None
    availability: Optional[str] = None
    expected_salary: Optional[str] = None
    summary: Optional[str] = None
    selling_points: Optional[List[str]] = None


class MatchGenerateRequest(BaseModel):
    """Generate matches for a job against active candidates."""

    candidate_ids: Optional[List[int]] = None  # None => all active candidates
    min_score: float = 0.0


class EmailGenerateRequest(BaseModel):
    job_id: int
    candidate_id: int
    contact_id: Optional[int] = None
    match_id: Optional[int] = None


class EmailUpdateRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None


class EmailStatusRequest(BaseModel):
    status: str
    approved_by: Optional[str] = "recruiter"


class CallGenerateRequest(BaseModel):
    job_id: int
    candidate_id: int
    contact_id: Optional[int] = None
    match_id: Optional[int] = None


class CallStatusRequest(BaseModel):
    status: str
    transcript: Optional[str] = None
    outcome_notes: Optional[str] = None
    human_handoff_needed: Optional[bool] = None
    meeting_requested: Optional[bool] = None
    approved_by: Optional[str] = "recruiter"


class ContactApprovalRequest(BaseModel):
    approved_for_outreach: bool
    approved_by: Optional[str] = "recruiter"


class SuppressionRequest(BaseModel):
    scope: str            # company | domain | email | contact
    value: str
    reason: Optional[str] = None
