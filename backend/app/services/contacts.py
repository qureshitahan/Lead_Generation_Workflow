"""Contact discovery + ranking (Milestone 3).

Ranks contacts by how useful their role is for our pitch. For small companies a
founder/CTO is often the best entry point; for larger companies a recruiter or
talent-acquisition lead usually is. All discovered contacts start unapproved.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import resolve_apollo_phone_webhook_url, settings
from app.models.company import Company
from app.models.contact import Contact
from app.models.enums import AuditAction, EnrichmentStatus, PhoneRevealStatus
from app.services.audit import log_action
from app.services.enrichment import get_enrichment_provider
from app.services.enrichment.base import EnrichmentContact

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
    "vice president of engineering": 86,
    "vice president, engineering": 86,
    "vice president engineering": 86,
    "cto": 88,
    "chief technology officer": 88,
    "founder": 85,
    "co-founder": 85,
    "head of talent": 82,
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
    is_leader = any(
        k in title_l
        for k in ("cto", "chief technology", "founder", "vp", "vice president", "head of", "director")
    )
    is_recruiter = any(k in title_l for k in ("recruiter", "talent", "hr", "people"))
    if employee_count is not None:
        if employee_count <= SMALL_COMPANY_THRESHOLD and is_leader:
            base += 8
            reason_parts.append("leader preferred at small company")
        elif employee_count > SMALL_COMPANY_THRESHOLD and is_recruiter:
            base += 6
            reason_parts.append("recruiter preferred at larger company")

    return min(100.0, base), "; ".join(reason_parts) + "."


def enrich_and_find_contacts(
    db: Session, company: Company, *, max_contacts: Optional[int] = None
) -> List[Contact]:
    """Enrich a company and create ranked contact rows. Returns newly created rows.

    When ``max_contacts`` is set (from the job page), it controls how many people
    Apollo searches for, how many are saved, and how many get email/phone reveal.
    When omitted (Companies page), defaults from settings apply.
    """
    provider = get_enrichment_provider()

    fetch_limit = (
        max(1, min(max_contacts, 25))
        if max_contacts is not None
        else settings.apollo_contacts_per_company
    )
    reveal_limit = (
        max(1, min(max_contacts, 25))
        if max_contacts is not None
        else settings.apollo_enrich_contacts_limit
    )
    save_limit = fetch_limit if max_contacts is not None else None

    company.enrichment_status = EnrichmentStatus.IN_PROGRESS
    db.flush()

    result = provider.enrich_company(
        company.name, linkedin_url=company.linkedin_url, domain=company.domain
    )
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
        company.name,
        domain=company.domain,
        target_titles=list(TARGET_TITLES),
        limit=fetch_limit if max_contacts is not None else None,
    )

    existing_ids = {c.external_id for c in company.contacts if c.external_id}
    existing_keys = {
        (c.name or "").strip().lower() + "|" + (c.title or "").strip().lower()
        for c in company.contacts
    }

    scored: List[tuple] = []
    for ec in found_contacts:
        # Prefer the stable Apollo person id for dedup; names can be obfuscated
        # (e.g. "Wiley Bl***p") in search results and only resolved on reveal.
        if ec.external_id and ec.external_id in existing_ids:
            continue
        key = (ec.name or "").strip().lower() + "|" + (ec.title or "").strip().lower()
        if not ec.external_id and key in existing_keys:
            continue
        if ec.external_id:
            existing_ids.add(ec.external_id)
        existing_keys.add(key)
        usefulness, reason = score_contact_title(ec.title, company.employee_count)
        scored.append((usefulness, reason, ec))

    scored.sort(key=lambda t: t[0], reverse=True)
    if save_limit is not None:
        scored = scored[:save_limit]

    phone_reveal_enabled = bool(
        settings.apollo_reveal_phone_number and resolve_apollo_phone_webhook_url()
    )

    revealed_count = 0
    phone_pending_count = 0
    top_ids: set[str] = set()
    if settings.apollo_reveal_contacts and scored:
        top = [ec for _, _, ec in scored]
        top_ids = {ec.external_id for ec in top if ec.external_id}
        if top:
            provider.reveal_contacts(top)
            revealed_count = sum(1 for ec in top if ec.email)

    created: List[Contact] = []
    for usefulness, reason, ec in scored:
        phone_status = None
        if phone_reveal_enabled and ec.external_id and ec.external_id in top_ids:
            if ec.phone:
                phone_status = PhoneRevealStatus.REVEALED
            else:
                phone_status = PhoneRevealStatus.PENDING
                phone_pending_count += 1

        contact = Contact(
            company_id=company.id,
            name=ec.name,
            title=ec.title,
            email=ec.email,
            email_status=ec.email_status,
            phone=ec.phone,
            phone_reveal_status=phone_status,
            linkedin_url=ec.linkedin_url,
            external_id=ec.external_id,
            source=result.source,
            confidence_score=ec.confidence_score,
            usefulness_score=usefulness,
            rank_reason=reason,
        )
        db.add(contact)
        created.append(contact)

    db.flush()

    # Reveal emails for existing top contacts (e.g. prior run saved 10, user now asks for 2).
    extra_revealed, extra_phones = _reveal_top_company_contacts(
        db, company, provider, reveal_limit, phone_reveal_enabled
    )
    revealed_count += extra_revealed
    phone_pending_count += extra_phones

    log_action(
        db,
        AuditAction.ENRICHMENT,
        entity_type="company",
        entity_id=company.id,
        summary=(
            f"Enriched via {result.source}; created {len(created)} contact(s), "
            f"revealed {revealed_count} email(s), {phone_pending_count} phone(s) pending."
        ),
        detail={
            "enrichment_source": result.source,
            "contacts": len(created),
            "emails_revealed": revealed_count,
            "phones_pending": phone_pending_count,
            "max_contacts": max_contacts,
        },
    )
    return created


def _reveal_top_company_contacts(
    db: Session,
    company: Company,
    provider,
    limit: int,
    phone_reveal_enabled: bool,
) -> tuple[int, int]:
    """Reveal email/phone for up to ``limit`` existing contacts missing email."""
    if not settings.apollo_reveal_contacts or limit <= 0:
        return 0, 0

    ranked = sorted(
        company.contacts,
        key=lambda c: -(c.usefulness_score or 0),
    )[:limit]
    to_reveal: List[EnrichmentContact] = []
    targets: List[Contact] = []
    for contact in ranked:
        if not contact.external_id:
            continue
        needs_email = not contact.email
        needs_phone = bool(
            phone_reveal_enabled
            and not contact.phone
            and contact.phone_reveal_status
            not in (PhoneRevealStatus.PENDING, PhoneRevealStatus.REVEALED)
        )
        if not needs_email and not needs_phone:
            continue
        to_reveal.append(
            EnrichmentContact(
                name=contact.name,
                title=contact.title,
                email=contact.email,
                external_id=contact.external_id,
                domain=company.domain,
                linkedin_url=contact.linkedin_url,
            )
        )
        targets.append(contact)

    if not to_reveal:
        return 0, 0

    provider.reveal_contacts(to_reveal)
    revealed = 0
    phones_pending = 0
    for contact, ec in zip(targets, to_reveal):
        if ec.email and not contact.email:
            contact.email = ec.email
            contact.email_status = ec.email_status
            revealed += 1
        elif ec.email_status and not contact.email_status:
            contact.email_status = ec.email_status
        if ec.phone:
            contact.phone = ec.phone
            contact.phone_reveal_status = PhoneRevealStatus.REVEALED
        elif phone_reveal_enabled and contact.external_id:
            contact.phone_reveal_status = PhoneRevealStatus.PENDING
            phones_pending += 1
        if ec.name:
            contact.name = ec.name
        if ec.linkedin_url:
            contact.linkedin_url = ec.linkedin_url

    db.flush()
    return revealed, phones_pending
