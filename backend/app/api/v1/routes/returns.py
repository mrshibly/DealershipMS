import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import SuccessResponse
from app.schemas.return_log import ReturnLogCreate, ReturnLogRead
from app.services import return_service

router = APIRouter(prefix="/returns", tags=["returns"])

@router.get("", response_model=SuccessResponse[List[ReturnLogRead]])
async def list_returns(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("returns", "view")),
):
    returns = await return_service.list_returns(db)
    
    enriched = []
    for r in returns:
        rr = ReturnLogRead.model_validate(r)
        rr.invoice_no = r.invoice.invoice_no if r.invoice else None
        rr.product_name = r.product.name_en if r.product else None
        enriched.append(rr)
        
    return SuccessResponse(data=enriched)

@router.post("", response_model=SuccessResponse[ReturnLogRead], status_code=201)
async def create_return(
    body: ReturnLogCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("returns", "create")),
):
    try:
        ret = await return_service.create_return(db, body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    rr = ReturnLogRead.model_validate(ret)
    rr.invoice_no = ret.invoice.invoice_no if ret.invoice else None
    rr.product_name = ret.product.name_en if ret.product else None
    
    return SuccessResponse(data=rr, message="Return logged successfully and stock adjusted.")
