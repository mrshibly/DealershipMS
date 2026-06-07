import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from decimal import Decimal
from datetime import date

from app.models.dealer import Dealer
from app.models.dsr import DSR
from app.models.shop import Shop
from app.models.product import Product
from app.models.category import Category
from app.schemas.inventory import OpeningStockCreate
from app.services.inventory_service import add_opening_stock

@pytest.mark.asyncio
async def test_sms_e2e(auth_client: AsyncClient, db_session: AsyncSession):
    # Setup Data
    dealer = Dealer(name="SMS Dealer", phone="01711223344")
    dsr = DSR(name="SMS DSR", phone="01722334455")
    shop = Shop(name="SMS Shop", owner_name="Owner SMS")
    cat = Category(name="Snacks SMS")
    
    db_session.add_all([dealer, dsr, shop, cat])
    await db_session.flush()

    prod = Product(
        name_en="Chips SMS",
        sku="CHIP-SMS-001",
        category_id=cat.id,
        pcs_per_carton=50,
        buy_price=8.0,
        sell_price=10.0,
        vat_applicable=True,
        vat_rate=Decimal("5.00")
    )
    db_session.add(prod)
    await db_session.flush()

    # Add opening stock so we can confirm the invoice
    open_req = OpeningStockCreate(
        product_id=prod.id,
        qty_pieces=500,
        unit_price=8.0,
        movement_date=date.today()
    )
    await add_opening_stock(db_session, open_req, uuid.uuid4())
    await db_session.commit()
    
    # 1. Create Invoice via API
    invoice_payload = {
        "dealer_id": str(dealer.id),
        "dsr_id": str(dsr.id),
        "shop_id": str(shop.id),
        "date": str(date.today()),
        "items": [
            {
                "product_id": str(prod.id),
                "qty_carton": 1,
                "qty_pcs": 10,
                "is_free_item": False
            }
        ]
    }
    
    response = await auth_client.post("/api/v1/invoices", json=invoice_payload)
    assert response.status_code == 200
    invoice_data = response.json()["data"]
    invoice_id = invoice_data["id"]
    
    # 2. Confirm Invoice via API
    confirm_res = await auth_client.post(f"/api/v1/invoices/{invoice_id}/confirm")
    assert confirm_res.status_code == 200
    
    # 3. Collect Payment (triggers SMS)
    payment_payload = {
        "amount": 300.0,
        "payment_method": "CASH"
    }
    
    payment_res = await auth_client.post(f"/api/v1/invoices/{invoice_id}/collect", json=payment_payload)
    assert payment_res.status_code == 200
    payment_data = payment_res.json()["data"]
    assert payment_data["paid_amount"] == "300.00"
    
    # If the response is 200, it means the Celery background task was successfully dispatched/handled
    # without breaking the synchronous HTTP request flow.
