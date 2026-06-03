"""Role profiles that drive relevance scoring.

Each profile defines the keywords that make a job a strong match, supporting
skills that add confidence, and negative signals that indicate an adjacent-but-
wrong role (e.g. game developer or petroleum engineer when targeting AI roles).

This is intentionally data-driven: tweak these lists to tune relevance without
touching the scoring logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class RoleProfile:
    name: str
    # Strong title signals — presence in the title is a near-certain match.
    title_keywords: List[str]
    # Supporting skills/terms that raise confidence when found in the body.
    skill_keywords: List[str] = field(default_factory=list)
    # Terms that indicate an adjacent but wrong role; reduce the score.
    negative_keywords: List[str] = field(default_factory=list)


# Keyed by the canonical role name used in TARGET_ROLES.
ROLE_PROFILES: Dict[str, RoleProfile] = {
    "Software Engineer": RoleProfile(
        name="Software Engineer",
        title_keywords=[
            "software engineer",
            "software developer",
            "backend engineer",
            "full stack",
            "fullstack",
            "full-stack",
            "frontend engineer",
            "sde",
        ],
        skill_keywords=[
            "python",
            "java",
            "typescript",
            "javascript",
            "go",
            "react",
            "node",
            "api",
            "microservices",
            "distributed systems",
        ],
        negative_keywords=[
            "game developer",
            "unreal engine",
            "graphics programmer",
            "petroleum",
            "field engineer",
            "sales engineer",
        ],
    ),
    "AI Engineer": RoleProfile(
        name="AI Engineer",
        title_keywords=[
            "ai engineer",
            "artificial intelligence engineer",
            "applied ai",
            "generative ai engineer",
            "llm engineer",
        ],
        skill_keywords=[
            "llm",
            "large language model",
            "nlp",
            "pytorch",
            "tensorflow",
            "transformers",
            "rag",
            "openai",
            "hugging face",
            "prompt",
            "machine learning",
        ],
        negative_keywords=[
            "game",
            "graphics programmer",
            "petroleum",
            "hardware",
            "ai sales",
            "ai trainer (contract)",
        ],
    ),
    "Machine Learning Engineer": RoleProfile(
        name="Machine Learning Engineer",
        title_keywords=[
            "machine learning engineer",
            "ml engineer",
            "mlops",
            "deep learning engineer",
        ],
        skill_keywords=[
            "pytorch",
            "tensorflow",
            "scikit",
            "model training",
            "feature engineering",
            "mlops",
            "model deployment",
            "nlp",
            "computer vision",
        ],
        negative_keywords=[
            "game developer",
            "petroleum",
            "mechanical engineer",
            "data entry",
        ],
    ),
    "Data Engineer": RoleProfile(
        name="Data Engineer",
        title_keywords=[
            "data engineer",
            "data platform engineer",
            "etl developer",
            "analytics engineer",
        ],
        skill_keywords=[
            "spark",
            "airflow",
            "kafka",
            "snowflake",
            "etl",
            "dbt",
            "data pipeline",
            "sql",
            "warehouse",
        ],
        negative_keywords=[
            "data entry",
            "data analyst (non-technical)",
            "petroleum",
            "game",
        ],
    ),
}
