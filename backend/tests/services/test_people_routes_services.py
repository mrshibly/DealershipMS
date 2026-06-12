import pytest
import uuid
from decimal import Decimal

from app.schemas.dealer import DealerCreate, DealerUpdate
from app.schemas.shop import ShopCreate, ShopUpdate
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.schemas.route import RouteCreate, RouteUpdate
from app.services.route_service import (
    list_routes, get_route, create_route, update_route, delete_route
)
from app.services.dealer_service import (
    list_dealers, get_dealer, create_dealer, update_dealer, delete_dealer
)
from app.services.shop_service import (
    list_shops, get_shop, create_shop, update_shop, delete_shop, list_shops_by_dealer
)
from app.services.supplier_service import (
    list_suppliers, get_supplier, create_supplier, update_supplier, delete_supplier
)

@pytest.mark.asyncio
async def test_route_service(db_session):
    user_id = uuid.uuid4()
    
    # Create
    route_in = RouteCreate(name="Route South", area="Dhaka South", description="South path")
    route = await create_route(db_session, route_in, user_id)
    assert route.name == "Route South"

    # Get
    fetched = await get_route(db_session, route.id)
    assert fetched is not None
    assert fetched.area == "Dhaka South"

    # List
    routes, total = await list_routes(db_session, search="South")
    assert total == 1
    assert routes[0].name == "Route South"

    # Update
    route_up = RouteUpdate(name="Route South Updated")
    updated = await update_route(db_session, route.id, route_up)
    assert updated.name == "Route South Updated"

    # Delete
    deleted = await delete_route(db_session, route.id)
    assert deleted is True
    assert await get_route(db_session, route.id) is None

@pytest.mark.asyncio
async def test_dealer_and_shop_services(db_session):
    user_id = uuid.uuid4()
    
    # Setup Route
    route_in = RouteCreate(name="Dhaka Central", area="Dhaka")
    route = await create_route(db_session, route_in, user_id)

    # Create Dealer
    dealer_in = DealerCreate(
        name="Dealer Central",
        phone="01911223344",
        address="Dhaka Address",
        district="Dhaka",
        route_id=route.id,
        trade_license="LIC-001",
        is_active=True
    )
    dealer = await create_dealer(db_session, dealer_in, user_id)
    assert dealer.name == "Dealer Central"
    assert dealer.route_name == "Dhaka Central"

    # Fetch Dealer
    fetched_dealer = await get_dealer(db_session, dealer.id)
    assert fetched_dealer is not None

    # List Dealers
    dealers, total = await list_dealers(db_session, search="Central")
    assert total == 1

    # Update Dealer
    dealer_up = DealerUpdate(name="Dealer Central Updated")
    updated_dealer = await update_dealer(db_session, dealer.id, dealer_up)
    assert updated_dealer.name == "Dealer Central Updated"

    # Create Shop
    shop_in = ShopCreate(
        dealer_id=dealer.id,
        name="Central Retail Shop",
        address="Road 5",
        shop_type="Retailer",
        owner_name="Karim",
        is_active=True
    )
    shop = await create_shop(db_session, shop_in, user_id)
    assert shop.name == "Central Retail Shop"
    assert shop.dealer_name == "Dealer Central Updated"

    # Fetch Shop
    fetched_shop = await get_shop(db_session, shop.id)
    assert fetched_shop is not None

    # List Shops
    shops, total_s = await list_shops(db_session, search="Retail")
    assert total_s == 1

    # List by Dealer
    by_dealer = await list_shops_by_dealer(db_session, dealer.id)
    assert len(by_dealer) == 1

    # Update Shop
    shop_up = ShopUpdate(name="Central Shop Updated")
    updated_shop = await update_shop(db_session, shop.id, shop_up)
    assert updated_shop.name == "Central Shop Updated"

    # Delete Shop
    assert await delete_shop(db_session, shop.id) is True
    assert await get_shop(db_session, shop.id) is None

    # Delete Dealer
    assert await delete_dealer(db_session, dealer.id) is True
    assert await get_dealer(db_session, dealer.id) is None

@pytest.mark.asyncio
async def test_supplier_service(db_session):
    user_id = uuid.uuid4()

    # Create
    sup_in = SupplierCreate(
        name="BD Supplier",
        contact="Mr. Rahim",
        phone="01811223344",
        address="Chittagong",
        district="Chittagong",
        vat_no="VAT-001",
        is_active=True
    )
    supplier = await create_supplier(db_session, sup_in, user_id)
    assert supplier.name == "BD Supplier"

    # Fetch
    fetched = await get_supplier(db_session, supplier.id)
    assert fetched is not None

    # List
    sups, total = await list_suppliers(db_session, search="BD")
    assert total == 1

    # Update
    sup_up = SupplierUpdate(name="BD Supplier Updated")
    updated = await update_supplier(db_session, supplier.id, sup_up)
    assert updated.name == "BD Supplier Updated"

    # Delete
    assert await delete_supplier(db_session, supplier.id) is True
    assert await get_supplier(db_session, supplier.id) is None
