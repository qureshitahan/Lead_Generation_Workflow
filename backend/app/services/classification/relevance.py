"""Relevance classifier.

Scores how well a job matches the recruiter's target roles on a 0-100 scale and
returns the best-matching role plus a human-readable explanation.

Scoring model (transparent and tunable):
  * Title contains a role's title keyword  -> strong base score (+60)
  * Each supporting skill keyword in body   -> +6 (capped)
  * Each negative keyword                    -> -25
  * No title match but skills present        -> partial score from skills only
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.core.config import settings
from app.services.classification.role_profiles import ROLE_PROFILES, RoleProfile


@dataclass
class RelevanceResult:
    score: float                 # 0-100
    matched_role: Optional[str]
    reason: str


TITLE_MATCH_BASE = 60.0
SKILL_POINTS = 6.0
SKILL_CAP = 36.0
NEGATIVE_PENALTY = 25.0


def _score_role(title: str, body: str, profile: RoleProfile) -> tuple[float, List[str]]:
    notes: List[str] = []
    score = 0.0

    title_hits = [kw for kw in profile.title_keywords if kw in title]
    if title_hits:
        score += TITLE_MATCH_BASE
        notes.append(f"title matches '{title_hits[0]}'")

    skill_hits = [kw for kw in profile.skill_keywords if kw in body]
    if skill_hits:
        gained = min(len(skill_hits) * SKILL_POINTS, SKILL_CAP)
        score += gained
        notes.append(f"{len(skill_hits)} relevant skill(s): {', '.join(skill_hits[:5])}")

    neg_hits = [kw for kw in profile.negative_keywords if kw in title or kw in body]
    if neg_hits:
        score -= NEGATIVE_PENALTY * len(neg_hits)
        notes.append(f"negative signal(s): {', '.join(neg_hits[:3])}")

    return score, notes


def classify_relevance(
    title: Optional[str],
    description: Optional[str],
    target_roles: Optional[List[str]] = None,
) -> RelevanceResult:
    """Return the best relevance match across the configured target roles."""
    target_roles = target_roles or settings.target_roles
    title_l = (title or "").lower()
    body_l = (description or "").lower()

    best_score = 0.0
    best_role: Optional[str] = None
    best_notes: List[str] = []

    for role_name in target_roles:
        profile = ROLE_PROFILES.get(role_name)
        if not profile:
            # Unknown role: fall back to a simple substring check on the title.
            if role_name.lower() in title_l:
                if TITLE_MATCH_BASE > best_score:
                    best_score = TITLE_MATCH_BASE
                    best_role = role_name
                    best_notes = [f"title contains '{role_name}'"]
            continue

        score, notes = _score_role(title_l, body_l, profile)
        if score > best_score:
            best_score = score
            best_role = profile.name
            best_notes = notes

    # Clamp to 0-100.
    final = max(0.0, min(100.0, best_score))

    if best_role and final > 0:
        reason = f"Best match: {best_role} ({final:.0f}/100). " + "; ".join(best_notes) + "."
    else:
        reason = (
            "No target role matched the title or description; "
            "likely irrelevant to current search."
        )
    return RelevanceResult(score=round(final, 1), matched_role=best_role, reason=reason)
