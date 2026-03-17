from __future__ import annotations

import re
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.literature import (
    EvidenceCardCreate,
    EvidenceCardOut,
    EvidenceCardUpdate,
    LiteratureItemCreate,
    LiteratureItemOut,
    LiteratureItemUpdate,
)
from app.services import literature_service, project_service

router = APIRouter(
    prefix="/api/projects/{project_id}/literature",
    tags=["literature"],
)

# ---------------------------------------------------------------------------
# Shared dependency: verify project exists
# ---------------------------------------------------------------------------

def _get_project_or_404(project_id: UUID, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ---------------------------------------------------------------------------
# Literature items
# ---------------------------------------------------------------------------

@router.get("/items/", response_model=List[LiteratureItemOut])
def list_literature_items(
    project_id: UUID,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    return literature_service.get_literature_items(db, project_id, skip=skip, limit=limit)


@router.post(
    "/items/",
    response_model=LiteratureItemOut,
    status_code=status.HTTP_201_CREATED,
)
def create_literature_item(
    project_id: UUID,
    data: LiteratureItemCreate,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    item = literature_service.create_literature_item(db, project_id, data)
    # Auto-run extraction stub if URL is provided
    if item.doi_or_url:
        item = literature_service.run_extraction_on_item(db, item)
    return item


@router.get("/items/{item_id}", response_model=LiteratureItemOut)
def get_literature_item(
    project_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    item = literature_service.get_literature_item(db, project_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Literature item not found")
    return item


@router.patch("/items/{item_id}", response_model=LiteratureItemOut)
def update_literature_item(
    project_id: UUID,
    item_id: UUID,
    data: LiteratureItemUpdate,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    item = literature_service.get_literature_item(db, project_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Literature item not found")
    return literature_service.update_literature_item(db, item, data)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_literature_item(
    project_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    item = literature_service.get_literature_item(db, project_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Literature item not found")
    literature_service.delete_literature_item(db, item)


# ---------------------------------------------------------------------------
# PDF upload → store + auto-extract
# ---------------------------------------------------------------------------

@router.post(
    "/items/{item_id}/upload-pdf",
    response_model=LiteratureItemOut,
)
def upload_pdf(
    project_id: UUID,
    item_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    item = literature_service.get_literature_item(db, project_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Literature item not found")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted")

    # Sanitize filename
    safe_name = re.sub(r"[^\w.\-]", "_", file.filename)
    content = file.file.read()
    pdf_path = literature_service.save_pdf(project_id, safe_name, content)

    # Persist path
    item.pdf_path = pdf_path
    db.commit()
    db.refresh(item)

    # Run extraction stub
    item = literature_service.run_extraction_on_item(db, item)
    return item


# ---------------------------------------------------------------------------
# Trigger extraction manually (re-run)
# ---------------------------------------------------------------------------

@router.post("/items/{item_id}/extract", response_model=LiteratureItemOut)
def run_extraction(
    project_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    item = literature_service.get_literature_item(db, project_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Literature item not found")
    if not item.pdf_path and not item.doi_or_url:
        raise HTTPException(
            status_code=422,
            detail="Item has no PDF or URL to extract from",
        )
    return literature_service.run_extraction_on_item(db, item)


# ---------------------------------------------------------------------------
# Evidence cards  (scoped to project; optionally filtered by literature item)
# ---------------------------------------------------------------------------

@router.get("/evidence/", response_model=List[EvidenceCardOut])
def list_evidence_cards(
    project_id: UUID,
    literature_item_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    return literature_service.get_evidence_cards(
        db, project_id, literature_item_id=literature_item_id
    )


@router.post(
    "/evidence/",
    response_model=EvidenceCardOut,
    status_code=status.HTTP_201_CREATED,
)
def create_evidence_card(
    project_id: UUID,
    data: EvidenceCardCreate,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    # Validate literature_item_id belongs to this project if provided
    if data.literature_item_id:
        source = literature_service.get_literature_item(
            db, project_id, data.literature_item_id
        )
        if not source:
            raise HTTPException(
                status_code=404,
                detail="Referenced literature item not found in this project",
            )
    return literature_service.create_evidence_card(db, project_id, data)


@router.get("/evidence/{card_id}", response_model=EvidenceCardOut)
def get_evidence_card(
    project_id: UUID,
    card_id: UUID,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    card = literature_service.get_evidence_card(db, project_id, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Evidence card not found")
    return card


@router.patch("/evidence/{card_id}", response_model=EvidenceCardOut)
def update_evidence_card(
    project_id: UUID,
    card_id: UUID,
    data: EvidenceCardUpdate,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    card = literature_service.get_evidence_card(db, project_id, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Evidence card not found")
    return literature_service.update_evidence_card(db, card, data)


@router.delete("/evidence/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence_card(
    project_id: UUID,
    card_id: UUID,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    card = literature_service.get_evidence_card(db, project_id, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Evidence card not found")
    literature_service.delete_evidence_card(db, card)
