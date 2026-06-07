import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from decimal import Decimal
from datetime import date

from app.models.dealer import Dealer
from app.models.product import Product
from app.models.category import Category
from app.schemas.inventory import OpeningStockCreate
from app.services.inventory_service import add_opening_stock

@pytest.mark.asyncio
async def test_returns_e2e(auth_client: AsyncClient, db_session: AsyncSession):
    # Setup Dealer and Product
    dealer = Dealer(name="Dealer 1", phone="01711223344")
    cat = Category(name="Electronics")
    db_session.add_all([dealer, cat])
    await db_session.flush()

    prod = Product(
        name_en="Phone",
        sku="PHN-001",
        category_id=cat.id,
        pcs_per_carton=10,
        buy_price=5000.0,
        sell_price=6000.0,
    )
    db_session.add(prod)
    await db_session.commit()
    await db_session.refresh(dealer)
    await db_session.refresh(prod)

    from app.models.invoice import Invoice, InvoiceStatus, InvoiceItem
    inv = Invoice(
        invoice_no="INV-RET-001",
        dealer_id=dealer.id,
        date=date.today(),
        subtotal=Decimal("6000.00"),
        grand_total=Decimal("6000.00"),
        status=InvoiceStatus.CONFIRMED,
        created_by=uuid.uuid4()
    )
    db_session.add(inv)
    await db_session.flush()

    inv_item = InvoiceItem(
        invoice_id=inv.id,
        product_id=prod.id,
        qty_carton=0,
        qty_pcs=10,
        total_pieces=10,
        unit_price=Decimal("600.00"),
        vat_rate=Decimal("0.00"),
        vat_amount=Decimal("0.00"),
        line_total=Decimal("6000.00"),
        is_free_item=False
    )
    db_session.add(inv_item)
    await db_session.commit()
    await db_session.refresh(inv)

    # 1. Create Return
    payload = {
        "invoice_id": str(inv.id),
        "product_id": str(prod.id),
        "qty_returned": 5,
        "reason": "Defective",
        "return_date": str(date.today())
    }

    response = await auth_client.post("/api/v1/returns", json=payload)
    if response.status_code != 201:
        print(response.json())
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["qty_returned"] == 5

    # 2. List Returns
    response = await auth_client.get("/api/v1/returns")
    assert response.status_code == 200
    data_list = response.json()["data"]
    assert len(data_list) > 0
    assert data_list[-1]["product_id"] == str(prod.id)
    assert data_list[-1]["qty_returned"] == 5
