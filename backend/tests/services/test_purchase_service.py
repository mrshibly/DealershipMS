import pytest
import uuid
from datetime import date
from decimal import Decimal

from app.models.supplier import Supplier
from app.models.category import Category
from app.models.product import Product
from app.models.purchase import PurchaseStatus
from app.schemas.purchase import PurchaseCreate, PurchaseItemCreate
from app.services.purchase_service import (
    create_purchase,
    receive_purchase,
    cancel_purchase,
    list_purchases,
    get_purchase,
)

@pytest.mark.asyncio
async def test_purchase_lifecycle(db_session):
    user_id = uuid.uuid4()

    # 1. Setup supplier, category, product
    supplier = Supplier(name="Test Supplier", phone="01800000000")
    category = Category(name="Test Category")
    db_session.add_all([supplier, category])
    await db_session.flush()

    product = Product(
        name_en="Prod P",
        name_bn="Prod P BN",
        sku="SKU-P",
        buy_price=Decimal("10.00"),
        sell_price=Decimal("15.00"),
        low_stock_threshold=5,
        category_id=category.id,
        pcs_per_carton=10,
        vat_applicable=False
    )
    db_session.add(product)
    await db_session.flush()
    await db_session.commit()

    # 2. Create Purchase (DRAFT)
    item_in = PurchaseItemCreate(
        product_id=product.id,
        qty_carton=5,  # 50 pcs
        qty_pcs=5,     # 5 pcs -> Total 55 pcs
        buy_price=Decimal("10.00")
    )
    purchase_in = PurchaseCreate(
        supplier_id=supplier.id,
        purchase_date=date.today(),
        invoice_no="PUR-2026-001",
        discount=Decimal("20.00"),
        items=[item_in],
        notes="First purchase"
    )

    purchase_raw = await create_purchase(db_session, purchase_in, user_id)
    purchase = await get_purchase(db_session, purchase_raw.id)
    assert purchase.status == PurchaseStatus.DRAFT
    # Total = 55 * 10 - 20 discount = 530
    assert purchase.total == Decimal("530.00")
    assert len(purchase.items) == 1

    # 3. List purchases
    purchases, total = await list_purchases(db_session, supplier_id=supplier.id, status="DRAFT")
    assert total == 1
    assert purchases[0].invoice_no == "PUR-2026-001"

    # 4. Receive Purchase
    received_raw = await receive_purchase(db_session, purchase.id, Decimal("500.00"), user_id)
    received = await get_purchase(db_session, received_raw.id)
    assert received.status == PurchaseStatus.RECEIVED
    assert received.paid == Decimal("500.00")

    # 5. Check if stock movements were created
    from app.services.inventory_service import get_stock_level
    stock = await get_stock_level(db_session, product)
    assert stock["qty_pieces"] == 55

    # 6. Try cancelling received purchase -> should raise error
    with pytest.raises(ValueError):
        await cancel_purchase(db_session, purchase.id)

    # 7. Create another purchase and cancel it
    purchase_in_2 = PurchaseCreate(
        supplier_id=supplier.id,
        purchase_date=date.today(),
        invoice_no="PUR-2026-002",
        discount=Decimal("0.00"),
        items=[item_in],
        notes="To be cancelled"
    )
    purchase_2_raw = await create_purchase(db_session, purchase_in_2, user_id)
    cancelled = await cancel_purchase(db_session, purchase_2_raw.id)
    assert cancelled.status == PurchaseStatus.CANCELLED
