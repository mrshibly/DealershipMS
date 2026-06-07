import pytest
import uuid
from decimal import Decimal
from datetime import date

from app.models.dealer import Dealer
from app.models.dsr import DSR
from app.models.shop import Shop
from app.models.product import Product
from app.models.category import Category
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate
from app.schemas.collection import CollectPaymentRequest
from app.services.invoice_service import create_invoice, confirm_invoice, collect_payment
from app.models.invoice import InvoiceStatus

@pytest.fixture
async def setup_data(db_session):
    # Mock entities
    dealer = Dealer(name="Dealer 1", phone="01711")
    dsr = DSR(name="DSR 1", phone="01722")
    shop = Shop(name="Shop 1", owner_name="Owner 1")
    cat = Category(name="Snacks")
    
    db_session.add_all([dealer, dsr, shop, cat])
    await db_session.flush()
    
    dsr.dealer_id = dealer.id
    shop.dsr_id = dsr.id
    
    prod = Product(
        name_en="Chips", 
        sku="CHIP-001",
        category_id=cat.id, 
        pcs_per_carton=50, 
        buy_price=8.0,
        sell_price=10.0,
        vat_applicable=True,
        vat_rate=Decimal("5.00")
    )
    db_session.add(prod)
    await db_session.flush()

    from app.schemas.inventory import OpeningStockCreate
    from app.services.inventory_service import add_opening_stock
    open_req = OpeningStockCreate(
        product_id=prod.id,
        qty_pieces=500,
        unit_price=8.0,
        movement_date=date.today()
    )
    await add_opening_stock(db_session, open_req, uuid.uuid4())
    await db_session.commit()
    
    return {
        "dealer": dealer,
        "dsr": dsr,
        "shop": shop,
        "product": prod
    }

@pytest.mark.asyncio
async def test_invoice_creation_and_confirmation(db_session, setup_data):
    data = setup_data
    
    user_id = uuid.uuid4()
    
    # 1. Create Invoice
    invoice_req = InvoiceCreate(
        dealer_id=data["dealer"].id,
        dsr_id=data["dsr"].id,
        shop_id=data["shop"].id,
        date=date.today(),
        items=[
            InvoiceItemCreate(
                product_id=data["product"].id,
                qty_carton=1, # 50 pcs
                qty_pcs=10    # 10 pcs -> Total 60 pcs
            )
        ]
    )
    
    # Expected: 60 pcs * 10 BDT = 600 BDT
    # VAT = 5% of 600 = 30 BDT
    # Grand Total = 630 BDT
    
    invoice = await create_invoice(db_session, invoice_req, user_id)
    
    assert invoice.status == InvoiceStatus.DRAFT
    assert invoice.grand_total == Decimal("630.00")
    assert len(invoice.items) == 1
    assert invoice.items[0].total_pieces == 60
    
    # 2. Confirm Invoice (deducts stock)
    confirmed_inv = await confirm_invoice(db_session, invoice.id, user_id)
    assert confirmed_inv.status == InvoiceStatus.CONFIRMED
    
    # Check stock (500 - 60 = 440)
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    prod = (await db_session.execute(select(Product).options(selectinload(Product.category)).where(Product.id == data["product"].id))).scalar_one()
    from app.services.inventory_service import get_stock_level
    stock_data = await get_stock_level(db_session, prod)
    assert stock_data["qty_pieces"] == 440
    
    # 3. Collect Payment
    payment_req = CollectPaymentRequest(
        amount=Decimal("300.00"),
        payment_method="CASH"
    )
    paid_inv = await collect_payment(db_session, invoice.id, payment_req, user_id)
    assert paid_inv.status == InvoiceStatus.PARTIAL
    assert paid_inv.paid_amount == Decimal("300.00")
    
    # Full payment
    payment_req_2 = CollectPaymentRequest(
        amount=Decimal("330.00"),
        payment_method="CASH"
    )
    paid_inv_full = await collect_payment(db_session, invoice.id, payment_req_2, user_id)
    assert paid_inv_full.status == InvoiceStatus.PAID


@pytest.mark.asyncio
async def test_update_draft_invoice(db_session, setup_data):
    from app.services.invoice_service import update_invoice
    from fastapi import HTTPException
    
    data = setup_data
    user_id = uuid.uuid4()
    
    # Create a draft invoice
    invoice_req = InvoiceCreate(
        dealer_id=data["dealer"].id,
        dsr_id=data["dsr"].id,
        shop_id=data["shop"].id,
        date=date.today(),
        items=[
            InvoiceItemCreate(
                product_id=data["product"].id,
                qty_carton=1,
                qty_pcs=0
            )
        ]
    )
    invoice = await create_invoice(db_session, invoice_req, user_id)
    assert invoice.status == InvoiceStatus.DRAFT
    assert invoice.grand_total == Decimal("525.00") # 50 * 10 * 1.05
    
    # Update draft invoice with new items and discount
    update_req = InvoiceCreate(
        dealer_id=data["dealer"].id,
        dsr_id=data["dsr"].id,
        shop_id=data["shop"].id,
        date=date.today(),
        discount=Decimal("50.00"),
        items=[
            InvoiceItemCreate(
                product_id=data["product"].id,
                qty_carton=2, # 100 pcs -> 100 * 10 * 1.05 = 1050
                qty_pcs=0
            )
        ]
    )
    
    updated_inv = await update_invoice(db_session, invoice.id, update_req, user_id)
    assert updated_inv.status == InvoiceStatus.DRAFT
    assert updated_inv.grand_total == Decimal("1000.00") # 1050 - 50 discount
    assert len(updated_inv.items) == 1
    assert updated_inv.items[0].total_pieces == 100
    
    # Confirm it
    await confirm_invoice(db_session, invoice.id, user_id)
    
    # Try updating confirmed invoice -> should fail
    with pytest.raises(HTTPException) as exc_info:
        await update_invoice(db_session, invoice.id, update_req, user_id)
    assert exc_info.value.status_code == 400
    assert "Only DRAFT invoices can be updated/adjusted" in exc_info.value.detail
