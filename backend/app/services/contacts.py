"""Contact discovery + ranking (Milestone 3).

Ranks contacts by how useful their role is for our pitch. For small companies a
founder/CTO is often the best entry point; for larger companies a recruiter or
talent-acquisition lead usually is. All discovered contacts start unapproved.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.models.enums import AuditAction, EnrichmentStatus
from app.services.audit import log_action
from app.services.enrichment import get_enrichment_provider

# Target titles with a base usefulness weight (0-100). Higher = better entry point.
TARGET_TITLES = {
    "talent acquisition": 80,
    "technical recruiter": 82,
    "recruiter": 70,
    "hr manager": 60,
    "people operations": 58,
    "hiring manager": 75,
    "engineering manager": 78,
    "director of engineering": 84,
    "vp engineering": 86,
    "vp of engineering": 86,
    "cto": 88,
    "founder": 85,
    "co-founder": 85,
    "head of ai": 88,
    "head of machine learning": 88,
    "head of engineering": 84,
}

SMALL_COMPANY_THRESHOLD = 50  # employees


def score_contact_title(title: Optional[str], employee_count: Optional[int]) -> tuple[float, str]:
    """Return (usefulness_score, reason) for a contact title given company size."""
    if not title:
        return 40.0, "No title available; default mid-low usefulness."
    title_l = title.lower()

    base = 45.0
    matched_key = None
    for key, weight in TARGET_TITLES.items():
        if key in title_l:
            if weight > base:
                base = float(weight)
                matched_key = key

    reason_parts = []
    if matched_key:
        reason_parts.append(f"matches target role '{matched_key}'")
    else:
        reason_parts.append("title not in target list")

    # Adjust for company size: leaders better at small cos, recruiters at large.
    is_leader = any(k in title_l for k in ("cto", "founder", "vp", "head of", "director"))
    is_recruiter = any(k in title_l for k in ("recruiter", "talent", "hr", "people"))
    if employee_count is not None:
        if employee_count <= SMALL_COMPANY_THRESHOLD and is_leader:
            base += 8
            reason_parts.append("leader preferred at small company")
        elif employee_count > SMALL_COMPANY_THRESHOLD and is_recruiter:
            base += 6
            reason_parts.append("recruiter preferred at larger company")

    return min(100.0, base), "; ".join(reason_parts) + "."


def enrich_and_find_contacts(db: Session, company: Company) -> List[Contact]:
    """Enrich a company and create ranked contact rows. Returns created contacts."""
    provider = get_enrichment_provider()

    company.enrichment_status = EnrichmentStatus.IN_PROGRESS
    db.flush()

    result = provider.enrich_company(company.name, linkedin_url=company.linkedin_url)
    if result.found:
        company.domain = company.domain or result.domain
        company.website = company.website or result.website
        company.linkedin_url = company.linkedin_url or result.linkedin_url
        company.industry = company.industry or result.industry
        company.employee_count = company.employee_count or result.employee_count
        company.headquarters = company.headquarters or result.headquarters
        company.phone = company.phone or result.phone
        company.funding = company.funding or result.funding
        company.revenue = company.revenue or result.revenue
        company.enrichment_status = EnrichmentStatus.ENRICHED
        company.enrichment_source = result.source
    else:
        company.enrichment_status = EnrichmentStatus.FAILED

    found_contacts = provider.find_contacts(
        company.name, domain=company.domain, target_titles=list(TARGET_TITLES)
    )

    created: List[Contact] = []
    for ec in found_contacts:
        usefulness, reason = score_contact_title(ec.title, company.employee_count)
        contact = Contact(
            company_id=company.id,
            name=ec.name,
            title=ec.title,
            email=ec.email,
            phone=ec.phone,
            linkedin_url=ec.linkedin_url,
            source=result.source,
            confidence_score=ec.confidence_score,
            usefulness_score=usefulness,
            rank_reason=reason,
        )
        db.add(contact)
        created.append(contact)

    db.flush()
    log_action(
        db,
        AuditAction.ENRICHMENT,
        entity_type="company",
        entity_id=company.id,
        summary=f"Enriched via {result.source}; created {len(created)} contact(s).",
        detail={"enrichment_source": result.source, "contacts": len(created)},
    )
    return created
