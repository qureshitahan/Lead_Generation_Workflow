"""Job import endpoints: file upload and pasted text."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.entities import ImportSummary
from app.schemas.requests import ImportPasteRequest
from app.services.import_service import import_jobs

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/file", response_model=ImportSummary)
async def import_from_file(
    source: str = Form("brightdata"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a CSV/JSON export from a job source (e.g. Bright Data)."""
    content = await file.read()
    try:
        result = import_jobs(
            db,
            source=source,
            content=content,
            content_type=file.content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ImportSummary(**result.__dict__)


@router.post("/paste", response_model=ImportSummary)
def import_from_paste(payload: ImportPasteRequest, db: Session = Depends(get_db)):
    """Import jobs from pasted CSV/JSON text."""
    try:
        result = import_jobs(
            db,
            source=payload.source,
            content=payload.content,
            content_type=payload.content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ImportSummary(**result.__dict__)
