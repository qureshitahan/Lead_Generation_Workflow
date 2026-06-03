"""Direct-employer vs staffing/recruiting classifier.

Critical for the business: we generally do NOT want to contact another
recruiting/staffing firm. This classifier inspects the company name, industry,
job description language, and job poster title for staffing red flags.

Returns:
  is_direct_employer, is_staffing_or_recruiting, confidence (0-100), explanation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EmployerResult:
    is_direct_employer: bool
    is_staffing_or_recruiting: bool
    confidence: float
    explanation: str


# Strong phrases that almost always indicate a staffing/recruiting intermediary.
STRONG_RED_FLAGS = [
    "our client is seeking",
    "our client is looking",
    "on behalf of our client",
    "on behalf of a client",
    "our financial services client",
    "client is seeking",
    "for our client",
    "rpo",
    "recruitment process outsourcing",
    "executive search",
    "contract staffing",
]

# Softer signals — meaningful but weaker on their own.
SOFT_RED_FLAGS = [
    "staffing",
    "recruiting",
    "recruitment",
    "talent solutions",
    "workforce solutions",
    "placement",
    "staffing agency",
    "consulting services firm",
    "talent acquisition firm",
    "headhunter",
    "search firm",
    "manpower",
    "talent partner",
]

# Terms in the COMPANY NAME that strongly imply a staffing firm.
COMPANY_NAME_FLAGS = [
    "staffing",
    "recruiting",
    "recruitment",
    "talent",
    "consulting",
    "solutions",
    "search",
    "resourcing",
    "personnel",
    "workforce",
]

# Job poster titles that suggest an agency recruiter (weaker signal).
POSTER_TITLE_FLAGS = [
    "agency recruiter",
    "staffing",
    "talent acquisition consultant",
    "recruitment consultant",
]


def _find(haystack: str, needles: List[str]) -> List[str]:
    return [n for n in needles if n in haystack]


def classify_direct_employer(
    company_name: Optional[str],
    description: Optional[str],
    industry: Optional[str] = None,
    job_poster_title: Optional[str] = None,
) -> EmployerResult:
    name_l = (company_name or "").lower()
    body_l = (description or "").lower()
    industry_l = (industry or "").lower()
    poster_l = (job_poster_title or "").lower()

    notes: List[str] = []
    score = 0  # higher => more likely staffing

    strong = _find(body_l, STRONG_RED_FLAGS)
    if strong:
        score += 60
        notes.append(f"description language: '{strong[0]}'")

    soft = _find(body_l + " " + industry_l, SOFT_RED_FLAGS)
    if soft:
        score += 15 * min(len(soft), 3)
        notes.append(f"staffing terms: {', '.join(sorted(set(soft))[:3])}")

    name_flags = _find(name_l, COMPANY_NAME_FLAGS)
    if name_flags:
        score += 25
        notes.append(f"company name contains '{name_flags[0]}'")

    if "staffing" in industry_l or "recruiting" in industry_l:
        score += 30
        notes.append(f"industry is '{industry}'")

    poster_flags = _find(poster_l, POSTER_TITLE_FLAGS)
    if poster_flags:
        score += 15
        notes.append(f"job poster title suggests agency: '{poster_flags[0]}'")

    is_staffing = score >= 40
    is_direct = not is_staffing

    # Confidence reflects how decisive the evidence is in either direction.
    if is_staffing:
        confidence = min(100.0, 50.0 + score / 2)
        explanation = "Likely a staffing/recruiting firm. " + "; ".join(notes) + "."
    else:
        # Few/no red flags -> probably a direct employer.
        confidence = max(45.0, 80.0 - score)
        explanation = (
            "Appears to be a direct employer; no strong staffing signals found."
            if not notes
            else "Leaning direct employer despite minor signals: " + "; ".join(notes) + "."
        )

    return EmployerResult(
        is_direct_employer=is_direct,
        is_staffing_or_recruiting=is_staffing,
        confidence=round(confidence, 1),
        explanation=explanation,
    )
