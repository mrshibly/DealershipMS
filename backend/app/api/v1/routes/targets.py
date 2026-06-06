import uuid
from typing import List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import SuccessResponse
from app.schemas.target import TargetCreate, TargetRead, TargetUpdate
from app.services import target_service

router = APIRouter(prefix="/targets", tags=["targets"])

@router.get("", response_model=SuccessResponse[List[TargetRead]])
async def list_targets(
    month: date = Query(None, description="Filter by month (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("targets", "view")),
):
    targets = await target_service.list_targets(db, month)
    
    # Calculate achieved amount dynamically
    enriched_targets = []
    for t in targets:
        achieved = await target_service.calculate_achieved_amount(db, t.dsr_id, t.target_month)
        tr = TargetRead.model_validate(t)
        tr.dsr_name = t.dsr.name if t.dsr else None
        tr.achieved_amount = achieved
        enriched_targets.append(tr)
        
    return SuccessResponse(data=enriched_targets)

@router.post("", response_model=SuccessResponse[TargetRead], status_code=201)
async def create_target(
    body: TargetCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("targets", "create")),
):
    target = await target_service.create_target(db, body)
    
    tr = TargetRead.model_validate(target)
    tr.dsr_name = target.dsr.name if target.dsr else None
    
    return SuccessResponse(data=tr, message="Target created successfully")

@router.put("/{target_id}", response_model=SuccessResponse[TargetRead])
async def update_target(
    target_id: uuid.UUID = Path(...),
    body: TargetUpdate = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("targets", "update")),
):
    target = await target_service.update_target(db, target_id, body)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
        
    tr = TargetRead.model_validate(target)
    tr.dsr_name = target.dsr.name if target.dsr else None
    
    return SuccessResponse(data=tr, message="Target updated")
