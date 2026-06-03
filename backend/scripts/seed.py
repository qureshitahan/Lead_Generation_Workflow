"""Seed script: end-to-end smoke test of the pipeline.

Run from the backend/ directory:  python -m scripts.seed

It will:
  1. Create tables.
  2. Import the sample Bright Data file (raw + normalized + classified).
  3. Create a sample candidate (parsed from resume text).
  4. Approve the top relevant direct-employer jobs and match the candidate.
  5. Generate an email draft for the best match.

Safe to run repeatedly (imports are deduplicated; candidate is upserted by name).
"""
from __future__ import annotations

import os
import sys

# Allow running as `python -m scripts.seed` or `python scripts/seed.py`.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select

from app.db.session import SessionLocal, init_db
from app.models.candidate import Candidate
from app.models.enums import JobStatus
from app.models.job import Job
from app.services.candidates import parse_resume
from app.services.email_generation import generate_email
from app.services.import_service import import_jobs
from app.services.matching import score_match

SAMPLE_FILE = os.path.join(os.path.dirname(__file__), "..", "sample_data", "brightdata_sample.json")

SAMPLE_RESUME = """
Jane Doe - Machine Learning Engineer
5 years of experience building production ML systems.
Skills: Python, PyTorch, NLP, LLM, transformers, RAG, MLOps, Docker, AWS, SQL.
Deployed NLP models and RAG pipelines at scale. Strong machine learning and deep learning background.
"""


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        with open(SAMPLE_FILE, "rb") as f:
            content = f.read()

        print("Importing sample Bright Data file...")
        result = import_jobs(db, source="brightdata", content=content, content_type="json")
        print(
            f"  imported={result.imported} duplicates={result.duplicates} "
            f"errors={result.errors}"
        )

        # Create / reuse a candidate.
        candidate = db.execute(
            select(Candidate).where(Candidate.name == "Jane Doe")
        ).scalar_one_or_none()
        if candidate is None:
            parsed = parse_resume(SAMPLE_RESUME)
            candidate = Candidate(
                name="Jane Doe",
                resume_text=SAMPLE_RESUME.strip(),
                target_roles=parsed.target_roles or ["machine learning engineer"],
                skills=parsed.skills,
                years_experience=parsed.years_experience,
                summary=parsed.summary,
                selling_points=parsed.selling_points,
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            print(f"Created candidate: {candidate.name} (skills: {candidate.skills})")

        # Approve relevant direct-employer jobs.
        jobs = db.execute(select(Job)).scalars().all()
        print("\nClassified jobs:")
        for job in jobs:
            tag = "DIRECT" if job.is_direct_employer else "STAFFING"
            print(
                f"  [{tag}] relevance={job.relevance_score:>5} | {job.title} "
                f"@ {job.company_name} -> {job.matched_role}"
            )
            if job.is_direct_employer and (job.relevance_score or 0) >= 50:
                job.status = JobStatus.APPROVED

        db.commit()

        # Match candidate to approved jobs and draft an email for the best.
        approved = [j for j in jobs if j.status == JobStatus.APPROVED]
        best = None
        best_score = -1.0
        for job in approved:
            outcome = score_match(job, candidate)
            if outcome.score > best_score:
                best_score = outcome.score
                best = (job, outcome)

        if best:
            job, outcome = best
            print(f"\nBest match: {job.title} @ {job.company_name} -> {outcome.score}/100")
            print(f"  Pitch: {outcome.pitch}")
            email = generate_email(job, job.company, None, candidate)
            print(f"\nDraft email subject: {email.subject}")
            print(email.body)

        print("\nSeed complete. Start the API with: uvicorn app.main:app --reload")
    finally:
        db.close()


if __name__ == "__main__":
    main()
