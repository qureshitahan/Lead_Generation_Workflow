"""Personalized outreach email drafting (Milestone 2).

Generates a concise, professional first-touch email for a job/company/contact/
candidate match. Deliberately light on resume detail; the goal is a soft CTA.
Drafts are never auto-sent — they require human approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.core.config import settings
from app.models.candidate import Candidate
from app.models.company import Company
from app.models.contact import Contact
from app.models.job import Job
from app.models.match import Match


@dataclass
class EmailContent:
    subject: str
    body: str


def _first_name(full_name: Optional[str]) -> str:
    if not full_name:
        return "there"
    return full_name.strip().split()[0]


def _candidate_strengths(candidate: Candidate, match: Optional[Match]) -> List[str]:
    """Prefer concrete, job-matched skills; fall back to the candidate's skills.

    Selling points are sentence fragments (e.g. "5+ years of experience"), so we
    only use raw skills here to keep the "across <skills>" phrasing clean.
    """
    if match and match.matched_skills:
        return list(match.matched_skills)[:3]
    return list((candidate.skills or [])[:3])


def generate_email(
    job: Job,
    company: Optional[Company],
    contact: Optional[Contact],
    candidate: Candidate,
    match: Optional[Match] = None,
) -> EmailContent:
    company_name = (company.name if company else None) or job.company_name or "your team"
    greeting_name = _first_name(contact.name if contact else None)
    strengths = _candidate_strengths(candidate, match)
    role = candidate.target_roles[0] if candidate.target_roles else "engineer"
    yrs = (
        f"{candidate.years_experience:.0f}+ years"
        if candidate.years_experience
        else "solid"
    )

    subject = f"Candidate for your {job.title} role"

    strengths_line = (
        f"They bring {yrs} of experience"
        + (f" across {', '.join(strengths)}" if strengths else "")
        + "."
    )

    body = (
        f"Hi {greeting_name},\n\n"
        f"I noticed {company_name} is hiring for a {job.title}. "
        f"We're working with a {role} who looks like a strong fit for that opening. "
        f"{strengths_line}\n\n"
        f"Would you be open to taking a quick look at their profile, or a brief call "
        f"to see if it makes sense to move forward?\n\n"
        f"Best regards,\n"
        f"{settings.outreach_from_name}"
    )

    return EmailContent(subject=subject, body=body)
