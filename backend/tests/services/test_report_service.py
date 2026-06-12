import pytest
from datetime import date, timedelta
from decimal import Decimal
import uuid

from app.models.category import Category
from app.models.product import Product
from app.models.invoice import Invoice, InvoiceStatus, InvoiceItem
from app.models.purchase import Purchase
from app.models.expense import Expense, ExpenseHead
from app.models.account import Account, AccountType
from app.models.stock_movement import StockMovement, MovementType
from app.models.collection import Collection
from app.services.report_service import (
    get_daybook,
    get_sales_report,
    get_product_sales_report,
    get_profit_report,
    get_vat_report,
    get_stock_movement_report,
)

@pytest.mark.asyncio
async def test_report_service_all(db_session):
    # Setup base entities
    category = Category(name="Cat R")
    db_session.add(category)
    await db_session.flush()

    product = Product(
        name_en="Prod R",
        name_bn="Prod R BN",
        sku="SKU-R",
        buy_price=Decimal("10.00"),
        sell_price=Decimal("15.00"),
        low_stock_threshold=5,
        category_id=category.id,
        vat_applicable=True,
        vat_rate=Decimal("15.00")
    )
    db_session.add(product)
    await db_session.flush()

    # Invoice with VAT
    invoice = Invoice(
        id=uuid.uuid4(),
        invoice_no="INV-2026-999",
        date=date.today(),
        subtotal=Decimal("15.00"),
        discount=Decimal("0.00"),
        vat_amount=Decimal("2.25"),
        grand_total=Decimal("17.25"),
        paid_amount=Decimal("10.00"),
        status=InvoiceStatus.CONFIRMED,
        created_by=uuid.uuid4()
    )
    db_session.add(invoice)
    await db_session.flush()

    item = InvoiceItem(
        invoice_id=invoice.id,
        product_id=product.id,
        qty_carton=0,
        qty_pcs=1,
        unit_price=Decimal("15.00"),
        line_total=Decimal("15.00"),
        total_pieces=1,
        is_free_item=False
    )
    db_session.add(item)

    # Collection
    collection = Collection(
        id=uuid.uuid4(),
        invoice_id=invoice.id,
        amount=Decimal("10.00"),
        collected_at=date.today(),
        payment_method="CASH",
        created_by=uuid.uuid4()
    )
    db_session.add(collection)

    # Purchase
    purchase = Purchase(
        id=uuid.uuid4(),
        purchase_date=date.today(),
        total=Decimal("50.00"),
        paid=Decimal("50.00"),
        created_by=uuid.uuid4(),
        status="RECEIVED"
    )
    db_session.add(purchase)

    # Account
    account = Account(
        name="Cash Register",
        type=AccountType.CASH,
        opening_balance=Decimal("200.00"),
        is_active=True,
        created_by=uuid.uuid4()
    )
    db_session.add(account)
    await db_session.flush()

    # ExpenseHead
    exp_head = ExpenseHead(name="Marketing")
    db_session.add(exp_head)
    await db_session.flush()

    # Expense
    expense = Expense(
        id=uuid.uuid4(),
        date=date.today(),
        amount=Decimal("5.00"),
        created_by=uuid.uuid4(),
        description="Delivery cost",
        head_id=exp_head.id,
        account_id=account.id
    )
    db_session.add(expense)

    # Stock movements
    sm1 = StockMovement(
        product_id=product.id,
        qty_pieces=10,
        movement_type=MovementType.OPENING_STOCK,
        movement_date=date.today(),
        is_approved=True,
        created_by=uuid.uuid4()
    )
    sm2 = StockMovement(
        product_id=product.id,
        qty_pieces=1,
        movement_type=MovementType.SALE,
        movement_date=date.today(),
        is_approved=True,
        created_by=uuid.uuid4()
    )
    db_session.add_all([sm1, sm2])

    await db_session.commit()

    # 1. Daybook
    daybook = await get_daybook(db_session, date.today())
    assert daybook["summary"]["total_inflow"] == 10.0
    assert daybook["summary"]["total_outflow"] == 55.0  # Expense (5) + Purchase paid (50)
    assert daybook["summary"]["total_sales_booked"] == 17.25

    # 2. Sales Report
    sales_rep = await get_sales_report(db_session, date.today() - timedelta(days=1), date.today())
    assert len(sales_rep) == 1
    assert sales_rep[0]["invoice_no"] == "INV-2026-999"

    # 3. Product Sales Report
    prod_sales = await get_product_sales_report(db_session, date.today() - timedelta(days=1), date.today())
    assert len(prod_sales) == 1
    assert prod_sales[0]["quantity_sold"] == 1
    assert prod_sales[0]["total_revenue"] == 15.0

    # 4. Profit Report
    profit_rep = await get_profit_report(db_session, date.today() - timedelta(days=1), date.today())
    assert len(profit_rep) == 1
    assert profit_rep[0]["sku"] == "SKU-R"
    assert profit_rep[0]["gross_profit"] == 5.0  # Revenue (15) - COGS (1 * 10 = 10)

    # 5. VAT Report
    vat_rep = await get_vat_report(db_session, date.today() - timedelta(days=1), date.today())
    assert len(vat_rep) == 1
    assert vat_rep[0]["vat_amount"] == 2.25

    # 6. Stock Movement Report
    stock_moves = await get_stock_movement_report(db_session, product.id)
    assert len(stock_moves) == 2
    assert stock_moves[0]["qty_change"] == 10
    assert stock_moves[1]["qty_change"] == -1
    assert stock_moves[1]["running_balance"] == 9
