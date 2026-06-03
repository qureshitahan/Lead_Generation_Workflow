"""Voice call script generation (Milestone 4 prep).

Generates a short, transparent call script for an approved lead. The agent must
never pretend to be human: the script includes an explicit AI-disclosure line to
use if asked. No calls are placed without human approval.
"""
from __future__ import annotations

from typing import List, Optional

from app.core.config import settings
from app.models.candidate import Candidate
from app.models.company import Company
from app.models.contact import Contact
from app.models.job import Job
from app.models.match import Match

# Transparency line the voice agent uses if asked whether it is AI.
AI_DISCLOSURE = (
    "Yes — I'm an AI assistant calling on behalf of the recruiting team. "
    "I can connect you with a human right away if you'd prefer."
)


def generate_call_script(
    job: Job,
    company: Optional[Company],
    contact: Optional[Contact],
    candidate: Candidate,
    match: Optional[Match] = None,
) -> str:
    company_name = (company.name if company else None) or job.company_name or "your company"
    skills: List[str] = []
    if match and match.matched_skills:
        skills = list(match.matched_skills)[:3]
    elif candidate.skills:
        skills = list(candidate.skills)[:3]
    skills_phrase = ", ".join(skills) if skills else "relevant areas"

    return (
        f"Hi, this is calling on behalf of {settings.outreach_from_name}. "
        f"I saw that {company_name} is hiring for a {job.title}. "
        f"We have a candidate with experience in {skills_phrase} who seems aligned "
        f"with the role. Who would be the best person to speak with about this opening?\n\n"
        f"[If asked whether this is AI]: {AI_DISCLOSURE}\n\n"
        f"[If interested]: Great — I'll have our manager follow up with the candidate's "
        f"profile. What's the best email or time for a quick call?\n\n"
        f"[If not interested]: Understood, thank you for your time. Have a great day."
    )
