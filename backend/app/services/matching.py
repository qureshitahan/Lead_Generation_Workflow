"""Candidate <-> job matching (Milestone 2).

Produces a 0-100 match score with matched/missing skills, concerns, a short
reason, and a ready-to-use pitch summary. Rule-based and transparent; can be
upgraded to embeddings/LLM later behind `score_match`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from app.models.candidate import Candidate
from app.models.job import Job
from app.services.candidates import KNOWN_SKILLS


@dataclass
class MatchResult:
    score: float
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    reason: str = ""
    pitch: str = ""


def _job_required_skills(job: Job) -> List[str]:
    """Pull skills the job mentions from our known-skill dictionary."""
    text = f"{job.title or ''} {job.description or ''}".lower()
    return [s for s in KNOWN_SKILLS if s in text]


def score_match(job: Job, candidate: Candidate) -> MatchResult:
    cand_skills = [s.lower() for s in (candidate.skills or [])]
    job_skills = _job_required_skills(job)

    matched = [s for s in job_skills if s in cand_skills]
    missing = [s for s in job_skills if s not in cand_skills]

    # --- Skill overlap component (0-70) ---
    if job_skills:
        skill_ratio = len(matched) / len(job_skills)
    else:
        # No detectable skills in the posting: lean on role alignment only.
        skill_ratio = 0.5
    skill_score = skill_ratio * 70

    # --- Role alignment component (0-30) ---
    role_score = 0.0
    cand_roles = [r.lower() for r in (candidate.target_roles or [])]
    job_role = (job.matched_role or job.title or "").lower()
    if cand_roles and any(r in job_role or job_role in r for r in cand_roles):
        role_score = 30.0
    elif job.matched_role and candidate.target_roles:
        role_score = 12.0  # partial: both classified, no direct overlap

    score = round(min(100.0, skill_score + role_score), 1)

    # --- Concerns ---
    concerns: List[str] = []
    if missing:
        concerns.append(f"Missing skills: {', '.join(missing[:5])}")
    if candidate.years_experience is not None and candidate.years_experience < 2:
        concerns.append("Candidate has limited years of experience")
    if not cand_skills:
        concerns.append("Candidate profile has no parsed skills")

    reason = (
        f"Matched {len(matched)}/{len(job_skills) or '0'} job skills "
        f"({', '.join(matched[:5]) or 'none'}); role alignment "
        f"{'yes' if role_score >= 30 else 'partial' if role_score else 'no'}."
    )

    pitch = _build_pitch(job, candidate, matched)

    return MatchResult(
        score=score,
        matched_skills=matched,
        missing_skills=missing,
        concerns=concerns,
        reason=reason,
        pitch=pitch,
    )


def _build_pitch(job: Job, candidate: Candidate, matched: List[str]) -> str:
    yrs = (
        f"{candidate.years_experience:.0f}+ years"
        if candidate.years_experience
        else "strong"
    )
    role = candidate.target_roles[0] if candidate.target_roles else "engineer"
    strengths = ", ".join(matched[:3]) if matched else ", ".join((candidate.skills or [])[:3])
    company = job.company_name or "your company"
    return (
        f"We have a {role} with {yrs} of experience"
        + (f" in {strengths}" if strengths else "")
        + f". Their background aligns with {company}'s {job.title} role"
        + (f", particularly around {strengths}." if strengths else ".")
    )
