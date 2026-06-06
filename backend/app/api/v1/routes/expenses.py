import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseHeadCreate,
    ExpenseHeadRead,
    ExpenseHeadUpdate,
    ExpenseRead,
)
from app.services import expense_service

router = APIRouter(prefix="/expenses", tags=["expenses"])

# --- Expense Heads ---

@router.get("/heads", response_model=SuccessResponse[list[ExpenseHeadRead]])
async def list_expense_heads(
    is_active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("expenses", "view")),
):
    heads = await expense_service.list_expense_heads(db, is_active=is_active)
    return SuccessResponse(data=heads)

@router.post("/heads", response_model=SuccessResponse[ExpenseHeadRead], status_code=201)
async def create_expense_head(
    body: ExpenseHeadCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("expenses", "create")),
):
    head = await expense_service.create_expense_head(db, body)
    return SuccessResponse(data=head, message="Expense Head created")

@router.put("/heads/{head_id}", response_model=SuccessResponse[ExpenseHeadRead])
async def update_expense_head(
    head_id: uuid.UUID = Path(...),
    body: ExpenseHeadUpdate = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("expenses", "update")),
):
    head = await expense_service.update_expense_head(db, head_id, body)
    if not head:
        raise HTTPException(status_code=404, detail="Expense Head not found")
    return SuccessResponse(data=head, message="Expense Head updated")


# --- Expenses ---

@router.get("", response_model=PaginatedResponse[ExpenseRead])
async def list_expenses(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    head_id: uuid.UUID | None = Query(default=None),
    account_id: uuid.UUID | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("expenses", "view")),
):
    expenses, total = await expense_service.list_expenses(
        db, page=page, per_page=per_page,
        head_id=head_id, account_id=account_id,
        date_from=date_from, date_to=date_to
    )
    
    enriched = []
    for exp in expenses:
        er = ExpenseRead.model_validate(exp)
        er.head_name = exp.head.name if exp.head else None
        er.account_name = exp.account.name if exp.account else None
        enriched.append(er)
        
    return PaginatedResponse(
        data=enriched, total=total, page=page,
        per_page=per_page, pages=ceil(total / per_page) if total else 0,
    )

@router.post("", response_model=SuccessResponse[ExpenseRead], status_code=201)
async def create_expense(
    body: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("expenses", "create")),
):
    try:
        expense = await expense_service.create_expense(db, body, current_user.id)
        
        er = ExpenseRead.model_validate(expense)
        er.head_name = expense.head.name if expense.head else None
        er.account_name = expense.account.name if expense.account else None
        
        return SuccessResponse(data=er, message="Expense created")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{expense_id}", response_model=SuccessResponse[dict])
async def delete_expense(
    expense_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("expenses", "delete")),
):
    deleted = await expense_service.delete_expense(db, expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
    return SuccessResponse(data={}, message="Expense deleted")
