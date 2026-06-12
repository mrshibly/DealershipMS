import pytest
from datetime import date, timedelta
from decimal import Decimal
import uuid

from app.models.product import Product
from app.models.category import Category
from app.models.invoice import Invoice, InvoiceStatus, InvoiceItem
from app.models.purchase import Purchase
from app.models.expense import Expense, ExpenseHead
from app.models.account import Account, AccountType
from app.models.target import Target
from app.models.dsr import DSR
from app.models.stock_movement import StockMovement, MovementType
from app.services.dashboard_service import get_daily_snapshot, get_analytics

@pytest.mark.asyncio
async def test_get_daily_snapshot(db_session):
    # Setup mock category and product
    category = Category(name="Category A")
    db_session.add(category)
    await db_session.flush()

    product1 = Product(
        name_en="Prod A",
        name_bn="Prod A BN",
        sku="SKU-A",
        buy_price=Decimal("10.00"),
        sell_price=Decimal("15.00"),
        low_stock_threshold=5,
        category_id=category.id,
        vat_applicable=False
    )
    product2 = Product(
        name_en="Prod B",
        name_bn="Prod B BN",
        sku="SKU-B",
        buy_price=Decimal("20.00"),
        sell_price=Decimal("30.00"),
        low_stock_threshold=10,
        category_id=category.id,
        vat_applicable=False
    )
    db_session.add_all([product1, product2])
    await db_session.flush()

    # Add stock movements (Product 1 has 10, Product 2 has 2 -> Alert)
    m1 = StockMovement(
        product_id=product1.id,
        qty_pieces=10,
        movement_type=MovementType.OPENING_STOCK,
        movement_date=date.today(),
        created_by=uuid.uuid4()
    )
    m2 = StockMovement(
        product_id=product2.id,
        qty_pieces=2,
        movement_type=MovementType.OPENING_STOCK,
        movement_date=date.today(),
        created_by=uuid.uuid4()
    )
    db_session.add_all([m1, m2])

    # Setup invoice
    invoice = Invoice(
        id=uuid.uuid4(),
        invoice_no="INV-2026-00001",
        date=date.today(),
        grand_total=Decimal("150.00"),
        paid_amount=Decimal("100.00"),
        status=InvoiceStatus.CONFIRMED,
        created_by=uuid.uuid4()
    )
    db_session.add(invoice)
    await db_session.flush()

    item = InvoiceItem(
        invoice_id=invoice.id,
        product_id=product1.id,
        qty_carton=0,
        qty_pcs=10,
        unit_price=Decimal("15.00"),
        line_total=Decimal("150.00"),
        total_pieces=10,
        is_free_item=False
    )
    db_session.add(item)

    # Setup purchase
    purchase = Purchase(
        id=uuid.uuid4(),
        purchase_date=date.today(),
        total=Decimal("80.00"),
        paid=Decimal("50.00"),
        created_by=uuid.uuid4(),
        status="RECEIVED"
    )
    db_session.add(purchase)

    # Setup accounts & expense
    account = Account(
        name="Cash Register",
        type=AccountType.CASH,
        opening_balance=Decimal("200.00"),
        is_active=True,
        created_by=uuid.uuid4()
    )
    db_session.add(account)
    await db_session.flush()

    exp_head = ExpenseHead(name="Office Supplies")
    db_session.add(exp_head)
    await db_session.flush()

    expense = Expense(
        id=uuid.uuid4(),
        date=date.today(),
        amount=Decimal("20.00"),
        created_by=uuid.uuid4(),
        description="Office supplies",
        head_id=exp_head.id,
        account_id=account.id
    )
    db_session.add(expense)

    # Setup DSR & target
    dsr = DSR(name="DSR A", phone="01712345678")
    db_session.add(dsr)
    await db_session.flush()

    target = Target(
        id=uuid.uuid4(),
        dsr_id=dsr.id,
        target_month=date(date.today().year, date.today().month, 1),
        target_amount=Decimal("1000.00")
    )
    db_session.add(target)

    await db_session.commit()

    # Get Daily Snapshot
    snapshot = await get_daily_snapshot(db_session, date.today() - timedelta(days=1), date.today() + timedelta(days=1))

    assert "kpis" in snapshot
    assert snapshot["kpis"]["net_sales"] == 150.0
    assert snapshot["kpis"]["net_purchase"] == 80.0
    # Current stock valuation check: prod A (10 pcs @ 10) + prod B (2 pcs @ 20) = 140
    assert snapshot["kpis"]["current_stock"] == 140.0
    # Profit calculation: Revenue (150) - COGS (10 * 10 = 100) - Expense (20) = 30
    assert snapshot["kpis"]["profit_loss"] == 30.0
    assert snapshot["kpis"]["dsr_sales_due"] == 50.0  # 150 - 100 paid
    assert snapshot["kpis"]["supplier_due"] == 30.0  # 80 - 50 paid
    assert snapshot["kpis"]["cash_balance"] == 180.0  # 200 opening - 20 expense

    # Check top selling products
    assert len(snapshot["top_selling"]) > 0
    assert snapshot["top_selling"][0]["product_name"] == "Prod A"

    # Check stock alerts (Prod B has 2 stock, threshold 10 -> Alert)
    assert len(snapshot["stock_alerts"]) == 1
    assert snapshot["stock_alerts"][0]["product_name"] == "Prod B"

    # Check sales vs target chart
    assert len(snapshot["sales_vs_target"]) == 12
    current_month_index = date.today().month - 1
    assert snapshot["sales_vs_target"][current_month_index]["actual_sales"] == 150.0
    assert snapshot["sales_vs_target"][current_month_index]["target"] == 1000.0

@pytest.mark.asyncio
async def test_get_analytics(db_session):
    res = await get_analytics(db_session, "monthly")
    assert res == []
