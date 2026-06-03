"""Candidate profile parsing (Milestone 2).

Heuristic parser that turns raw resume text into structured fields. It is
deliberately simple and rule-based for the MVP; an LLM parser can be slotted in
later behind the same `parse_resume` signature. Any explicitly provided fields
override the parsed values.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

# A pragmatic skill dictionary. Extend freely; matching is case-insensitive.
KNOWN_SKILLS = [
    "python", "java", "c++", "c#", "go", "golang", "rust", "javascript",
    "typescript", "react", "node", "node.js", "django", "flask", "fastapi",
    "sql", "postgresql", "mysql", "mongodb", "redis", "spark", "airflow",
    "kafka", "snowflake", "dbt", "etl", "aws", "gcp", "azure", "docker",
    "kubernetes", "terraform", "pytorch", "tensorflow", "scikit-learn",
    "keras", "nlp", "llm", "transformers", "hugging face", "rag", "openai",
    "computer vision", "mlops", "machine learning", "deep learning",
    "data engineering", "microservices", "graphql", "rest", "ci/cd",
]

ROLE_HINTS = [
    "software engineer", "ai engineer", "machine learning engineer",
    "ml engineer", "data engineer", "backend engineer", "full stack engineer",
    "data scientist", "mlops engineer",
]


@dataclass
class ParsedCandidate:
    skills: List[str] = field(default_factory=list)
    target_roles: List[str] = field(default_factory=list)
    years_experience: Optional[float] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    selling_points: List[str] = field(default_factory=list)


def _extract_skills(text: str) -> List[str]:
    found = []
    for skill in KNOWN_SKILLS:
        if re.search(r"\b" + re.escape(skill) + r"\b", text):
            found.append(skill)
    # De-dupe while preserving order, title-case for display.
    seen = set()
    out = []
    for s in found:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _extract_years(text: str) -> Optional[float]:
    # Matches "5 years", "5+ years", "5 yrs of experience".
    matches = re.findall(r"(\d{1,2})\+?\s*(?:years|yrs)", text)
    if matches:
        return float(max(int(m) for m in matches))
    return None


def _extract_roles(text: str) -> List[str]:
    return [role for role in ROLE_HINTS if role in text]


def parse_resume(resume_text: str) -> ParsedCandidate:
    """Extract structured data from raw resume text using simple heuristics."""
    text = (resume_text or "").lower()
    skills = _extract_skills(text)
    roles = _extract_roles(text)
    years = _extract_years(text)

    # Build a short summary + selling points from what we found.
    selling_points: List[str] = []
    if years:
        selling_points.append(f"{years:.0f}+ years of experience")
    if skills:
        selling_points.append("Strong skills: " + ", ".join(skills[:5]))
    if roles:
        selling_points.append("Targets: " + ", ".join(roles[:3]))

    summary = None
    if skills or roles:
        role_str = roles[0].title() if roles else "engineer"
        yrs = f"{years:.0f}+ years" if years else "relevant"
        summary = (
            f"{role_str} with {yrs} experience"
            + (f" in {', '.join(skills[:4])}" if skills else "")
            + "."
        )

    return ParsedCandidate(
        skills=skills,
        target_roles=roles,
        years_experience=years,
        location=None,
        summary=summary,
        selling_points=selling_points,
    )
