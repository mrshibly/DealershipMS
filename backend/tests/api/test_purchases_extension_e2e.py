import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from decimal import Decimal
from datetime import date

from app.models.supplier import Supplier
from app.models.account import Account, AccountType
from app.models.product import Product
from app.models.category import Category
from app.models.stock_movement import StockMovement, MovementType
from app.models.purchase_return import PurchaseReturnStatus


@pytest.mark.asyncio
async def test_supplier_payment_e2e(auth_client: AsyncClient, db_session: AsyncSession):
    # 1. Setup Supplier and Account
    supplier = Supplier(name="Test Supplier", phone="01799887766")
    account = Account(
        name="Cash Account",
        type=AccountType.CASH,
        opening_balance=Decimal("50000.00"),
        is_active=True
    )
    db_session.add_all([supplier, account])
    await db_session.commit()
    await db_session.refresh(supplier)
    await db_session.refresh(account)

    # 2. Record Payment
    payload = {
        "supplier_id": str(supplier.id),
        "account_id": str(account.id),
        "amount": "15000.00",
        "payment_date": str(date.today()),
        "description": "Partial payment for purchase return test"
    }
    
    response = await auth_client.post("/api/v1/supplier-payments", json=payload)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    payment_id = res_data["data"]["id"]

    # 3. List Payments
    response = await auth_client.get("/api/v1/supplier-payments")
    assert response.status_code == 200
    res_list = response.json()["data"]
    assert len(res_list) > 0
    assert res_list[0]["id"] == payment_id
    assert Decimal(res_list[0]["amount"]) == Decimal("15000.00")

    # 4. Void Payment
    response = await auth_client.post(f"/api/v1/supplier-payments/{payment_id}/void")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["is_deleted"] is True


@pytest.mark.asyncio
async def test_purchase_return_e2e(auth_client: AsyncClient, db_session: AsyncSession):
    # 1. Setup Supplier, Category, and Product
    supplier = Supplier(name="Return Supplier", phone="01799887755")
    cat = Category(name="Drinks")
    db_session.add_all([supplier, cat])
    await db_session.flush()

    product = Product(
        name_en="Mango Juice",
        sku="MGO-JUC",
        category_id=cat.id,
        pcs_per_carton=24,
        buy_price=20.0,
        sell_price=25.0,
    )
    db_session.add(product)
    await db_session.flush()

    # 2. Create inward stock movement so that we have stock to return
    inward_movement = StockMovement(
        product_id=product.id,
        movement_type=MovementType.OPENING_STOCK,
        qty_pieces=100,
        unit_price=Decimal("20.00"),
        movement_date=date.today(),
        is_approved=True,
        notes="Opening stock",
    )
    db_session.add(inward_movement)
    await db_session.commit()
    await db_session.refresh(product)

    # 3. Create Purchase Return (Draft)
    payload = {
        "supplier_id": str(supplier.id),
        "return_date": str(date.today()),
        "discount": "10.00",
        "notes": "Testing return workflow",
        "items": [
            {
                "product_id": str(product.id),
                "qty_carton": 1,
                "qty_pcs": 6,
                "return_price": "22.00"
            }
        ]
    }
    
    response = await auth_client.post("/api/v1/purchase-returns", json=payload)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    return_id = res_data["data"]["id"]
    assert res_data["data"]["status"] == PurchaseReturnStatus.DRAFT.value

    # 4. Get Return Details
    response = await auth_client.get(f"/api/v1/purchase-returns/{return_id}")
    assert response.status_code == 200
    res_detail = response.json()["data"]
    assert len(res_detail["items"]) == 1
    assert res_detail["items"][0]["total_pieces"] == 30 # 1 carton * 24 + 6 pcs = 30
    assert Decimal(res_detail["subtotal"]) == Decimal("660.00") # 30 * 22 = 660
    assert Decimal(res_detail["total_receivable"]) == Decimal("650.00") # 660 - 10 discount = 650

    # 5. Confirm Purchase Return
    response = await auth_client.post(f"/api/v1/purchase-returns/{return_id}/confirm")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == PurchaseReturnStatus.CONFIRMED.value

    # Check stock level (should be 100 - 30 = 70 pcs)
    from app.services.inventory_service import get_stock_level
    stock = await get_stock_level(db_session, product)
    assert stock["qty_pieces"] == 70
