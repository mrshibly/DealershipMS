import pytest
import uuid
from decimal import Decimal
from datetime import date

from app.models.dealer import Dealer
from app.models.account import Account, AccountType
from app.models.collection import Collection, PaymentMethod
from app.models.expense import Expense
from app.schemas.account import AccountCreate
from app.services.account_service import create_account, compute_balance

@pytest.mark.asyncio
async def test_account_creation_and_balance(db_session):
    dealer = Dealer(name="Dealer 1", phone="01711")
    db_session.add(dealer)
    await db_session.flush()
    
    from app.models.expense import ExpenseHead
    head = ExpenseHead(name="Office Supplies")
    db_session.add(head)
    
    # Create Account
    req = AccountCreate(
        name="Dealer Cash",
        type="CASH",
        opening_balance=Decimal("1000.00")
    )
    
    user_id = uuid.uuid4()
    account = await create_account(db_session, req, user_id)
    
    assert account.type == AccountType.CASH
    assert account.opening_balance == Decimal("1000.00")
    
    from app.models.invoice import Invoice, InvoiceStatus
    inv = Invoice(
        invoice_no="INV-TEST",
        dealer_id=dealer.id,
        date=date.today(),
        subtotal=Decimal("400.00"),
        grand_total=Decimal("400.00"),
        status=InvoiceStatus.CONFIRMED,
        created_by=user_id
    )
    db_session.add(inv)
    await db_session.flush()

    # Collections are not directly tied to accounts in the current schema
    # (they are tied to invoices). So they don't affect this specific compute_balance logic.
    
    # Add Expense (Outflow, decreases balance)
    exp = Expense(
        account_id=account.id,
        head_id=head.id,
        amount=Decimal("150.00"),
        date=date.today(),
        created_by=user_id
    )
    db_session.add(exp)
    await db_session.commit()
    
    # Check Balance (1000 - 150 = 850)
    balance = await compute_balance(db_session, account.id)
    assert balance == Decimal("850.00")
