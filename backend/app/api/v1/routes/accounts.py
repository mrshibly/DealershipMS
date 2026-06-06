import uuid
from math import ceil
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import SuccessResponse
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate
from app.services import account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("", response_model=SuccessResponse[list[dict]])
async def list_accounts(
    type: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("accounts", "view")),
):
    accounts = await account_service.get_accounts_with_balances(db, type=type, is_active=is_active)
    return SuccessResponse(data=accounts)


@router.get("/{account_id}", response_model=SuccessResponse[AccountRead])
async def get_account(
    account_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("accounts", "view")),
):
    account = await account_service.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Enrich with current balance
    balance = await account_service.compute_balance(db, account_id)
    account_read = AccountRead.model_validate(account)
    account_read.current_balance = float(balance)
    
    return SuccessResponse(data=account_read)


@router.post("", response_model=SuccessResponse[AccountRead], status_code=201)
async def create_account(
    body: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("accounts", "create")),
):
    account = await account_service.create_account(db, body, current_user.id)
    return SuccessResponse(data=account, message="Account created")


@router.put("/{account_id}", response_model=SuccessResponse[AccountRead])
async def update_account(
    account_id: uuid.UUID = Path(...),
    body: AccountUpdate = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("accounts", "update")),
):
    account = await account_service.update_account(db, account_id, body)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return SuccessResponse(data=account, message="Account updated")


@router.delete("/{account_id}", response_model=SuccessResponse[dict])
async def delete_account(
    account_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("accounts", "delete")),
):
    deleted = await account_service.delete_account(db, account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")
    return SuccessResponse(data={}, message="Account deleted")


@router.get("/{account_id}/balance", response_model=SuccessResponse[dict])
async def get_account_balance(
    account_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("accounts", "view")),
):
    try:
        balance = await account_service.compute_balance(db, account_id)
        return SuccessResponse(data={"balance": float(balance)})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
