import pytest
import uuid
from datetime import date

from app.models.product import Product
from app.models.category import Category
from app.models.stock_movement import MovementType
from app.schemas.inventory import StockAdjustmentCreate, OpeningStockCreate
from app.services.inventory_service import add_opening_stock, add_stock_adjustment, get_stock_level

@pytest.mark.asyncio
async def test_add_stock_and_get_stock(db_session):
    # Setup Category and Product
    cat = Category(name="Beverages")
    db_session.add(cat)
    await db_session.flush()
    
    prod = Product(
        name_en="Coke", 
        sku="COKE-001",
        category_id=cat.id, 
        pcs_per_carton=24, 
        buy_price=20.0,
        sell_price=25.0
    )
    db_session.add(prod)
    await db_session.commit()
    
    user_id = uuid.uuid4()
    
    # Opening stock
    open_req = OpeningStockCreate(
        product_id=prod.id,
        qty_pieces=100,
        unit_price=15.0,
        movement_date=date.today()
    )
    await add_opening_stock(db_session, open_req, user_id)
    
    # Reload prod with category eager-loaded
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    prod = (await db_session.execute(select(Product).options(selectinload(Product.category)).where(Product.id == prod.id))).scalar_one()

    # Check initial stock
    level = await get_stock_level(db_session, prod)
    assert level["qty_pieces"] == 100
    
    # Add stock
    adj_req = StockAdjustmentCreate(
        product_id=prod.id,
        movement_type=MovementType.ADJUSTMENT_IN,
        qty_pieces=50,
        unit_price=15.0,
        movement_date=date.today(),
        notes="Restock"
    )
    
    movement = await add_stock_adjustment(db_session, adj_req, user_id)
    
    assert movement.qty_pieces == 50
    assert movement.movement_type == MovementType.ADJUSTMENT_IN
    
    # Check updated stock
    prod = (await db_session.execute(select(Product).options(selectinload(Product.category)).where(Product.id == prod.id))).scalar_one()
    new_level = await get_stock_level(db_session, prod)
    assert new_level["qty_pieces"] == 150
