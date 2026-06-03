"""Contact listing and outreach-approval endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.contact import Contact
from app.models.enums import AuditAction
from app.schemas.entities import ContactOut, Page
from app.schemas.requests import ContactApprovalRequest
from app.services.audit import log_action

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=Page[ContactOut])
def list_contacts(
    db: Session = Depends(get_db),
    company_id: Optional[int] = None,
    approved: Optional[bool] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Contact)
    count_query = select(func.count()).select_from(Contact)
    filters = []
    if company_id is not None:
        filters.append(Contact.company_id == company_id)
    if approved is not None:
        filters.append(Contact.approved_for_outreach.is_(approved))
    for f in filters:
        query = query.where(f)
        count_query = count_query.where(f)

    query = query.order_by(Contact.usefulness_score.desc()).limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    total = db.execute(count_query).scalar_one()
    return Page[ContactOut](items=items, total=total, limit=limit, offset=offset)


@router.post("/{contact_id}/approval", response_model=ContactOut)
def set_approval(
    contact_id: int, payload: ContactApprovalRequest, db: Session = Depends(get_db)
):
    contact = db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact.approved_for_outreach = payload.approved_for_outreach
    log_action(
        db,
        AuditAction.CONTACT_APPROVAL,
        entity_type="contact",
        entity_id=contact.id,
        actor=payload.approved_by or "recruiter",
        summary=f"approved_for_outreach={payload.approved_for_outreach}",
    )
    db.commit()
    db.refresh(contact)
    return contact
