import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.contra import ContraEntryCreate, ContraEntryRead
from app.services import contra_service

router = APIRouter(prefix="/contra-entries", tags=["contra_entries"])

@router.get("", response_model=PaginatedResponse[ContraEntryRead])
async def list_contra_entries(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    from_account_id: uuid.UUID | None = Query(default=None),
    to_account_id: uuid.UUID | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("accounts", "view")),
):
    entries, total = await contra_service.list_contra_entries(
        db, page=page, per_page=per_page,
        from_account_id=from_account_id, to_account_id=to_account_id,
        date_from=date_from, date_to=date_to
    )
    
    enriched = []
    for entry in entries:
        er = ContraEntryRead.model_validate(entry)
        er.from_account_name = entry.from_account.name if entry.from_account else None
        er.to_account_name = entry.to_account.name if entry.to_account else None
        enriched.append(er)
        
    return PaginatedResponse(
        data=enriched, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )

@router.post("", response_model=SuccessResponse[ContraEntryRead], status_code=201)
async def create_contra_entry(
    body: ContraEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("accounts", "create")),
):
    try:
        entry = await contra_service.create_contra_entry(db, body, current_user.id)
        
        er = ContraEntryRead.model_validate(entry)
        er.from_account_name = entry.from_account.name if entry.from_account else None
        er.to_account_name = entry.to_account.name if entry.to_account else None
        
        return SuccessResponse(data=er, message="Contra Entry recorded")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{entry_id}", response_model=SuccessResponse[dict])
async def delete_contra_entry(
    entry_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("accounts", "delete")),
):
    deleted = await contra_service.delete_contra_entry(db, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contra Entry not found")
    return SuccessResponse(data={}, message="Contra Entry deleted")
