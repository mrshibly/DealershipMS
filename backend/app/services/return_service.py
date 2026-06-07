import uuid
from typing import List, Optional
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.return_log import ReturnLog
from app.models.stock_movement import StockMovement
from app.schemas.return_log import ReturnLogCreate
from app.models.product import Product
from app.models.stock_movement import MovementType

async def list_returns(db: AsyncSession) -> List[ReturnLog]:
    result = await db.execute(
        select(ReturnLog)
        .options(selectinload(ReturnLog.invoice), selectinload(ReturnLog.product))
        .order_by(ReturnLog.created_at.desc())
    )
    return list(result.scalars().all())

async def create_return(db: AsyncSession, data: ReturnLogCreate) -> ReturnLog:
    # 1. Create ReturnLog entry
    return_log = ReturnLog(
        invoice_id=data.invoice_id,
        product_id=data.product_id,
        qty_returned=data.qty_returned,
        reason=data.reason,
        return_date=data.return_date or date.today()
    )
    db.add(return_log)
    

        
    # 3. Create StockMovement
    movement = StockMovement(
        product_id=data.product_id,
        movement_type=MovementType.SALES_RETURN,
        qty_pieces=data.qty_returned,
        reference_id=data.invoice_id,
        movement_date=data.return_date or date.today(),
        notes=f"Sales Return: {data.reason or 'No reason provided'}",
        is_approved=True
    )
    db.add(movement)
    
    await db.commit()
    await db.refresh(return_log)
    
    # Fetch with relations for returning
    result = await db.execute(
        select(ReturnLog)
        .options(selectinload(ReturnLog.invoice), selectinload(ReturnLog.product))
        .where(ReturnLog.id == return_log.id)
    )
    return result.scalar_one()
