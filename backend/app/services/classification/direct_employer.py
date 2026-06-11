"""Direct-employer vs staffing/recruiting classifier.

Critical for the business: we generally do NOT want to contact another
recruiting/staffing firm. This classifier inspects the company name, industry,
job description language, and job poster title for staffing red flags.

Returns:
  is_direct_employer, is_staffing_or_recruiting, confidence (0-100), explanation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EmployerResult:
    is_direct_employer: bool
    is_staffing_or_recruiting: bool
    confidence: float
    explanation: str


# Multi-word phrases — substring match is safe.
STRONG_PHRASE_FLAGS = [
    "our client is seeking",
    "our client is looking",
    "on behalf of our client",
    "on behalf of a client",
    "our financial services client",
    "client is seeking",
    "for our client",
    "recruitment process outsourcing",
    "executive search firm",
    "contract staffing",
    "staffing agency",
    "recruiting firm",
    "talent acquisition firm",
    "we are hiring for our client",
    "hiring on behalf of",
]

# Short tokens / acronyms — must match as whole words (avoid "rpo" in "corporate").
STRONG_WORD_FLAGS = [
    "rpo",
]

SOFT_PHRASE_FLAGS = [
    "talent solutions",
    "workforce solutions",
    "staffing agency",
    "consulting services firm",
    "talent acquisition firm",
    "search firm",
    "talent partner",
    "contract-to-hire",
    "contract to hire",
]

SOFT_WORD_FLAGS = [
    "staffing",
    "headhunter",
    "manpower",
]

# Softer — only count in description when clearly agency context, not HR boilerplate.
SOFT_WORD_FLAGS_INDUSTRY_ONLY = [
    "recruiting",
    "recruitment",
]

# Company name must contain staffing-specific terms (not generic "consulting"/"solutions").
COMPANY_NAME_FLAGS = [
    "staffing",
    "recruiting",
    "recruitment",
    "resourcing",
    "personnel",
    "workforce",
    "headhunter",
    "manpower",
    "talent solutions",
    "executive search",
    "search partners",
    "search group",
]

POSTER_TITLE_FLAGS = [
    "agency recruiter",
    "staffing",
    "talent acquisition consultant",
    "recruitment consultant",
]

# LinkedIn / Bright Data industries that strongly indicate a real hiring company.
DIRECT_EMPLOYER_INDUSTRY_HINTS = [
    "banking",
    "financial services",
    "investment banking",
    "insurance",
    "capital markets",
    "asset management",
    "fintech",
    "health care",
    "healthcare",
    "hospital",
    "higher education",
    "government",
    "retail",
    "manufacturing",
    "automotive",
    "aerospace",
    "defense",
    "energy",
    "utilities",
    "telecommunications",
    "real estate",
    "hospitality",
    "construction",
    "pharmaceutical",
    "biotechnology",
]

STAFFING_INDUSTRY_HINTS = [
    "staffing and recruiting",
    "staffing & recruiting",
    "staffing/recruiting",
    "human resources services",
]


def _word_pattern(term: str) -> re.Pattern[str]:
    return re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)


def _find_phrases(haystack: str, phrases: List[str]) -> List[str]:
    return [p for p in phrases if p in haystack]


def _find_words(haystack: str, words: List[str]) -> List[str]:
    return [w for w in words if _word_pattern(w).search(haystack)]


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

    strong_phrases = _find_phrases(body_l, STRONG_PHRASE_FLAGS)
    strong_words = _find_words(body_l, STRONG_WORD_FLAGS)
    strong = strong_phrases + strong_words
    if strong:
        score += 60
        notes.append(f"description language: '{strong[0]}'")

    soft_phrases = _find_phrases(body_l + " " + industry_l, SOFT_PHRASE_FLAGS)
    soft_words = _find_words(body_l, SOFT_WORD_FLAGS)
    soft = soft_phrases + soft_words
    if soft:
        score += 15 * min(len(soft), 3)
        notes.append(f"staffing terms: {', '.join(sorted(set(soft))[:3])}")

    # "recruiting"/"recruitment" in industry field (LinkedIn category) is a strong signal.
    industry_recruit = _find_words(industry_l, SOFT_WORD_FLAGS_INDUSTRY_ONLY)
    if industry_recruit:
        score += 30
        notes.append(f"industry category: {', '.join(industry_recruit)}")

    name_flags = _find_words(name_l, COMPANY_NAME_FLAGS) + _find_phrases(
        name_l, ["talent solutions", "executive search"]
    )
    if name_flags:
        score += 25
        notes.append(f"company name contains '{name_flags[0]}'")

    if any(hint in industry_l for hint in STAFFING_INDUSTRY_HINTS):
        score += 40
        notes.append(f"industry is staffing/recruiting ('{industry}')")

    poster_flags = _find_phrases(poster_l, POSTER_TITLE_FLAGS) + _find_words(
        poster_l, ["staffing"]
    )
    if poster_flags:
        score += 15
        notes.append(f"job poster title suggests agency: '{poster_flags[0]}'")

    direct_industry = [
        h for h in DIRECT_EMPLOYER_INDUSTRY_HINTS if h in industry_l
    ]
    if direct_industry:
        score -= 35
        notes.append(
            f"industry suggests direct employer ({direct_industry[0]})"
        )

    # Need decisive evidence to label as staffing; direct-industry jobs need a higher bar.
    threshold = 50 if direct_industry else 40
    is_staffing = score >= threshold
    is_direct = not is_staffing

    if is_staffing:
        confidence = min(100.0, 50.0 + max(score, 0) / 2)
        explanation = "Likely a staffing/recruiting firm. " + "; ".join(notes) + "."
    else:
        confidence = max(45.0, 80.0 - max(score, 0))
        positive = [n for n in notes if "direct employer" in n]
        negative = [n for n in notes if "direct employer" not in n]
        if positive and not negative:
            explanation = (
                "Direct employer based on company industry/profile. "
                + "; ".join(positive)
                + "."
            )
        elif not notes:
            explanation = (
                "Appears to be a direct employer; no strong staffing signals found."
            )
        else:
            explanation = (
                "Leaning direct employer despite minor signals: "
                + "; ".join(negative)
                + "."
            )

    return EmployerResult(
        is_direct_employer=is_direct,
        is_staffing_or_recruiting=is_staffing,
        confidence=round(confidence, 1),
        explanation=explanation,
    )
