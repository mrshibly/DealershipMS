import pytest
import uuid
from decimal import Decimal

from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product_service import (
    list_categories,
    create_category,
    get_product,
    get_product_by_barcode,
    list_products,
    create_product,
    update_product,
    delete_product,
)

@pytest.mark.asyncio
async def test_category_service(db_session):
    user_id = uuid.uuid4()
    cat = await create_category(db_session, {"name": "Test Category"}, user_id)
    assert cat.name == "Test Category"
    
    categories = await list_categories(db_session)
    assert len(categories) == 1
    assert categories[0].name == "Test Category"

@pytest.mark.asyncio
async def test_product_crud_operations(db_session):
    user_id = uuid.uuid4()
    cat = await create_category(db_session, {"name": "Drinks"}, user_id)

    # 1. Create Product
    prod_data = ProductCreate(
        name_en="Soda",
        name_bn="সোডা",
        sku="SODA-001",
        category_id=cat.id,
        unit="piece",
        pcs_per_carton=24,
        buy_price=Decimal("15.00"),
        sell_price=Decimal("20.00"),
        mrp=Decimal("22.00"),
        vat_applicable=True,
        vat_rate=Decimal("15.00"),
        low_stock_threshold=5,
        is_active=True
    )
    
    product_enriched = await create_product(db_session, prod_data, user_id)
    assert product_enriched["name_en"] == "Soda"
    assert product_enriched["sku"] == "SODA-001"
    assert product_enriched["barcode"] is not None
    assert product_enriched["stock_qty_pieces"] == 0
    assert product_enriched["is_low_stock"] is True

    # 2. Get Product
    prod_id = product_enriched["id"]
    prod_db = await get_product(db_session, prod_id)
    assert prod_db is not None
    assert prod_db.name_en == "Soda"

    # 3. Get Product by Barcode
    prod_by_bc = await get_product_by_barcode(db_session, product_enriched["barcode"])
    assert prod_by_bc is not None
    assert prod_by_bc.id == prod_id

    # 4. List Products
    prods, total = await list_products(db_session, search="Soda", category_id=cat.id)
    assert total == 1
    assert prods[0]["name_en"] == "Soda"

    # 5. Update Product
    update_data = ProductUpdate(
        name_en="Diet Soda",
        buy_price=Decimal("16.00")
    )
    updated = await update_product(db_session, prod_id, update_data, user_id)
    assert updated["name_en"] == "Diet Soda"
    assert updated["buy_price"] == Decimal("16.00")

    # 6. Delete Product (Soft delete)
    deleted = await delete_product(db_session, prod_id)
    assert deleted is True

    prod_deleted = await get_product(db_session, prod_id)
    assert prod_deleted is None

@pytest.mark.asyncio
async def test_create_product_auto_sku(db_session):
    user_id = uuid.uuid4()
    cat = await create_category(db_session, {"name": "Drinks"}, user_id)

    # Create Product without specifying SKU
    prod_data = ProductCreate(
        name_en="Water",
        name_bn="পানি",
        sku="",
        category_id=cat.id,
        unit="piece",
        pcs_per_carton=24,
        buy_price=Decimal("10.00"),
        sell_price=Decimal("12.00"),
        mrp=Decimal("15.00"),
        vat_applicable=False,
        vat_rate=Decimal("0.00"),
        low_stock_threshold=5,
        is_active=True
    )
    
    product_enriched = await create_product(db_session, prod_data, user_id)
    assert product_enriched["sku"] is not None
    assert len(product_enriched["sku"]) > 0
