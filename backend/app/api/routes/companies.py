"""Company listing, detail, and enrichment trigger endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import Company
from app.models.contact import Contact
from app.schemas.entities import CompanyOut, ContactOut, Page
from app.services.contacts import enrich_and_find_contacts

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=Page[CompanyOut])
def list_companies(
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    direct_employer: Optional[bool] = None,
    enrichment_status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Company)
    count_query = select(func.count()).select_from(Company)
    filters = []
    if search:
        filters.append(Company.name.ilike(f"%{search}%"))
    if direct_employer is not None:
        filters.append(Company.is_direct_employer.is_(direct_employer))
    if enrichment_status:
        filters.append(Company.enrichment_status == enrichment_status)
    for f in filters:
        query = query.where(f)
        count_query = count_query.where(f)

    query = query.order_by(Company.created_at.desc()).limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    total = db.execute(count_query).scalar_one()
    return Page[CompanyOut](items=items, total=total, limit=limit, offset=offset)


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/{company_id}/enrich", response_model=list[ContactOut])
def enrich_company(company_id: int, db: Session = Depends(get_db)):
    """Enrich firmographics and discover ranked contacts (Milestone 3)."""
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    contacts = enrich_and_find_contacts(db, company)
    db.commit()
    for c in contacts:
        db.refresh(c)
    return contacts
