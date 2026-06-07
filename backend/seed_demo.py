"""
seed_demo.py - Seeds the database with rich demo data for all modules:
- Categories
- Suppliers
- Products
- Routes
- Dealers
- DSRs
- Targets
- Shops
- StockMovements (Opening Stock)
- Accounts
- ExpenseHeads & Expenses
- Invoices & InvoiceItems
- Collections
"""
import asyncio
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, delete

# Add app to path
sys.path.insert(0, ".")

from app.core.config import get_settings
from app.models import (
    Account, AccountType, Category, Collection, Dealer, DSR, ExpenseHead, Expense,
    Invoice, InvoiceItem, Product, Route, Shop, StockMovement, Supplier, Target, User
)
from app.models.collection import PaymentMethod
from app.models.invoice import InvoiceStatus
from app.models.stock_movement import MovementType

settings = get_settings()

async def clean_database(session: AsyncSession) -> None:
    print("Cleaning existing demo data...")
    # Delete in correct order to avoid foreign key constraint violations
    await session.execute(delete(Collection))
    await session.execute(delete(InvoiceItem))
    await session.execute(delete(Invoice))
    await session.execute(delete(StockMovement))
    await session.execute(delete(Product))
    await session.execute(delete(Category))
    await session.execute(delete(Shop))
    await session.execute(delete(Target))
    await session.execute(delete(DSR))
    await session.execute(delete(Dealer))
    await session.execute(delete(Route))
    await session.execute(delete(Expense))
    await session.execute(delete(ExpenseHead))
    await session.execute(delete(Account))
    await session.execute(delete(Supplier))
    print("Database cleaned.")

async def seed_demo() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSession_ = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSession_() as session:
        async with session.begin():
            # Get admin user
            result = await session.execute(select(User).where(User.email == "admin@dms.local"))
            admin = result.scalar_one_or_none()
            if not admin:
                print("Error: admin@dms.local not found. Please run seed.py first.")
                return
            admin_id = admin.id

            await clean_database(session)

            # 1. Seed Suppliers
            suppliers = [
                Supplier(
                    name="Pran-RFL Foods Ltd",
                    contact_person="Mizanur Rahman",
                    phone="+8801711223344",
                    email="mizan@pranrfl.com",
                    address="Pran Center, Middle Badda, Dhaka",
                    district="Dhaka",
                    vat_no="123456789-001",
                    opening_balance=Decimal("50000.00"),
                    created_by=admin_id
                ),
                Supplier(
                    name="Square Consumer Products Ltd",
                    contact_person="Tanvir Ahmed",
                    phone="+8801811556677",
                    email="tanvir@squaregroup.com",
                    address="Square Centre, 48 Mohakhali C/A, Dhaka",
                    district="Dhaka",
                    vat_no="987654321-002",
                    opening_balance=Decimal("25000.00"),
                    created_by=admin_id
                ),
                Supplier(
                    name="ACI Logistics Ltd",
                    contact_person="Rashedul Islam",
                    phone="+8801911990011",
                    email="rashed@aci-bd.com",
                    address="ACI Centre, Tejgaon, Dhaka",
                    district="Dhaka",
                    vat_no="456789123-003",
                    opening_balance=Decimal("0.00"),
                    created_by=admin_id
                )
            ]
            session.add_all(suppliers)
            await session.flush()
            print(f"Seeded {len(suppliers)} Suppliers")

            # 2. Seed Categories
            categories = [
                Category(name="Beverages", name_bn="পানীয়", description="Soft drinks, juices, and mineral water", created_by=admin_id),
                Category(name="Snacks", name_bn="স্ন্যাক্স", description="Chips, biscuits, and confectionery", created_by=admin_id),
                Category(name="Toiletries", name_bn="প্রসাধন সামগ্রী", description="Soaps, shampoos, and detergents", created_by=admin_id)
            ]
            session.add_all(categories)
            await session.flush()
            print(f"Seeded {len(categories)} Categories")

            # 3. Seed Products
            products = [
                Product(
                    name_en="Pran Mango Juice 250ml",
                    name_bn="প্রাণ ম্যাঙ্গো জুস ২৫০মি.লি.",
                    sku="PRN-MJ-250",
                    barcode="8941122334455",
                    category_id=categories[0].id,
                    unit="piece",
                    pcs_per_carton=24,
                    buy_price=Decimal("15.00"),
                    sell_price=Decimal("18.00"),
                    mrp=Decimal("20.00"),
                    vat_applicable=True,
                    vat_rate=Decimal("15.00"),
                    low_stock_threshold=100,
                    description="Sweet and refreshing mango juice",
                    created_by=admin_id
                ),
                Product(
                    name_en="Coca-Cola 500ml",
                    name_bn="কোকা-কোলা ৫০০মি.লি.",
                    sku="CCE-CC-500",
                    barcode="8941122334462",
                    category_id=categories[0].id,
                    unit="piece",
                    pcs_per_carton=24,
                    buy_price=Decimal("32.00"),
                    sell_price=Decimal("36.00"),
                    mrp=Decimal("40.00"),
                    vat_applicable=True,
                    vat_rate=Decimal("15.00"),
                    low_stock_threshold=200,
                    description="Standard Coca-Cola PET bottle",
                    created_by=admin_id
                ),
                Product(
                    name_en="Potato Crackers 25g",
                    name_bn="পটেটো ক্র্যাকার্স ২৫গ্রাম",
                    sku="PRN-PC-025",
                    barcode="8941122334479",
                    category_id=categories[1].id,
                    unit="piece",
                    pcs_per_carton=60,
                    buy_price=Decimal("8.00"),
                    sell_price=Decimal("9.00"),
                    mrp=Decimal("10.00"),
                    vat_applicable=True,
                    vat_rate=Decimal("5.00"),
                    low_stock_threshold=300,
                    description="Spicy potato crackers snacks",
                    created_by=admin_id
                ),
                Product(
                    name_en="Lex soap 100g",
                    name_bn="লেক্স সাবান ১০০গ্রাম",
                    sku="SQR-LX-100",
                    barcode="8941122334486",
                    category_id=categories[2].id,
                    unit="piece",
                    pcs_per_carton=48,
                    buy_price=Decimal("40.00"),
                    sell_price=Decimal("46.00"),
                    mrp=Decimal("50.00"),
                    vat_applicable=True,
                    vat_rate=Decimal("15.00"),
                    low_stock_threshold=50,
                    description="Premium beauty soap",
                    created_by=admin_id
                )
            ]
            session.add_all(products)
            await session.flush()
            print(f"Seeded {len(products)} Products")

            # 4. Seed Stock Movements (Opening Stock)
            # Give healthy stock levels to the products
            stock_date = date.today() - timedelta(days=10)
            stock_movements = [
                StockMovement(
                    product_id=products[0].id,
                    movement_type=MovementType.OPENING_STOCK,
                    qty_pieces=1200,  # 50 cartons
                    unit_price=products[0].buy_price,
                    movement_date=stock_date,
                    notes="Initial opening stock",
                    created_by=admin_id
                ),
                StockMovement(
                    product_id=products[1].id,
                    movement_type=MovementType.OPENING_STOCK,
                    qty_pieces=2400,  # 100 cartons
                    unit_price=products[1].buy_price,
                    movement_date=stock_date,
                    notes="Initial opening stock",
                    created_by=admin_id
                ),
                StockMovement(
                    product_id=products[2].id,
                    movement_type=MovementType.OPENING_STOCK,
                    qty_pieces=6000,  # 100 cartons
                    unit_price=products[2].buy_price,
                    movement_date=stock_date,
                    notes="Initial opening stock",
                    created_by=admin_id
                ),
                StockMovement(
                    product_id=products[3].id,
                    movement_type=MovementType.OPENING_STOCK,
                    qty_pieces=480,   # 10 cartons
                    unit_price=products[3].buy_price,
                    movement_date=stock_date,
                    notes="Initial opening stock",
                    created_by=admin_id
                )
            ]
            session.add_all(stock_movements)
            await session.flush()
            print(f"Seeded Opening Stock for all Products")

            # 5. Seed Routes
            routes = [
                Route(name="Dhanmondi Route", area="Dhaka West", description="Dhanmondi, Sobhanbagh, Kalabagan", created_by=admin_id),
                Route(name="Gulshan Route", area="Dhaka North", description="Gulshan 1, Gulshan 2, Banani", created_by=admin_id),
                Route(name="Mirpur Route", area="Dhaka North-West", description="Mirpur 1, 2, 10, Pallabi", created_by=admin_id)
            ]
            session.add_all(routes)
            await session.flush()
            print(f"Seeded {len(routes)} Routes")

            # 6. Seed Dealers
            dealers = [
                Dealer(
                    name="Dhanmondi General Store",
                    owner_name="Abul Kalam",
                    phone="+8801700000001",
                    address="House 12, Road 5, Dhanmondi, Dhaka",
                    district="Dhaka",
                    upazila="Dhanmondi",
                    trade_license="TL-DH-9912",
                    nid="NID-992122",
                    route_id=routes[0].id,
                    created_by=admin_id
                ),
                Dealer(
                    name="Gulshan Distribution Agency",
                    owner_name="Zahed Hasan",
                    phone="+8801700000002",
                    address="Plot 55, Gulshan Avenue, Dhaka",
                    district="Dhaka",
                    upazila="Gulshan",
                    trade_license="TL-GS-5511",
                    nid="NID-551221",
                    route_id=routes[1].id,
                    created_by=admin_id
                )
            ]
            session.add_all(dealers)
            await session.flush()
            print(f"Seeded {len(dealers)} Dealers")

            # 7. Seed DSRs
            dsrs = [
                DSR(
                    name="Rakib Hossain",
                    phone="+8801511223344",
                    nid="NID-88123211",
                    route_id=routes[0].id,
                    commission_rate=Decimal("2.50"),
                    joining_date=date.today() - timedelta(days=90),
                    created_by=admin_id
                ),
                DSR(
                    name="Jamil Uddin",
                    phone="+8801511556677",
                    nid="NID-88123299",
                    route_id=routes[1].id,
                    commission_rate=Decimal("3.00"),
                    joining_date=date.today() - timedelta(days=60),
                    created_by=admin_id
                )
            ]
            session.add_all(dsrs)
            await session.flush()
            print(f"Seeded {len(dsrs)} DSRs")

            # 8. Seed DSR Targets
            targets = [
                Target(
                    dsr_id=dsrs[0].id,
                    target_month=date(date.today().year, date.today().month, 1),
                    target_amount=Decimal("150000.00")
                ),
                Target(
                    dsr_id=dsrs[1].id,
                    target_month=date(date.today().year, date.today().month, 1),
                    target_amount=Decimal("200000.00")
                )
            ]
            session.add_all(targets)
            await session.flush()
            print(f"Seeded DSR Targets for current month")

            # 9. Seed Shops
            shops = [
                Shop(dealer_id=dealers[0].id, name="Bismillah Mart", owner_name="Al Amin", address="Dhanmondi 15", shop_type="Retailer", created_by=admin_id),
                Shop(dealer_id=dealers[0].id, name="Mollah Grocery", owner_name="Mollah Shafi", address="Kalabagan Bazar", shop_type="Retailer", created_by=admin_id),
                Shop(dealer_id=dealers[1].id, name="Gulshan Mega Superstore", owner_name="Sabbir Ahmed", address="Gulshan 2 Circle", shop_type="Wholesaler", created_by=admin_id)
            ]
            session.add_all(shops)
            await session.flush()
            print(f"Seeded {len(shops)} Shops")

            # 10. Seed Financial Accounts
            accounts = [
                Account(name="Cash Box (Dhanmondi HQ)", type=AccountType.CASH, opening_balance=Decimal("100000.00"), created_by=admin_id),
                Account(name="City Bank Ltd. A/C 101", type=AccountType.BANK, account_no="1102993882", opening_balance=Decimal("500000.00"), created_by=admin_id),
                Account(name="bKash Merchant Account", type=AccountType.MOBILE_BANKING, account_no="01799228833", opening_balance=Decimal("250000.00"), created_by=admin_id)
            ]
            session.add_all(accounts)
            await session.flush()
            print(f"Seeded {len(accounts)} Financial Accounts")

            # 11. Seed Expense Heads & Expenses
            expense_heads = [
                ExpenseHead(name="Office Rent", description="Monthly HQ Rent"),
                ExpenseHead(name="Vehicle Fuel", description="DSR Transport fuel"),
                ExpenseHead(name="DSR Commissions", description="Monthly commissions payout")
            ]
            session.add_all(expense_heads)
            await session.flush()

            expenses = [
                Expense(
                    head_id=expense_heads[0].id,
                    amount=Decimal("25000.00"),
                    date=date.today() - timedelta(days=5),
                    account_id=accounts[1].id,  # Bank
                    description="Office Rent for current month",
                    created_by=admin_id
                ),
                Expense(
                    head_id=expense_heads[1].id,
                    amount=Decimal("3200.00"),
                    date=date.today() - timedelta(days=2),
                    account_id=accounts[0].id,  # Cash
                    description="Fuel for Mirpur delivery van",
                    created_by=admin_id
                )
            ]
            session.add_all(expenses)
            await session.flush()
            print(f"Seeded Expense Heads and Expenses")

            # 12. Seed Invoices & Invoice Items
            # We want one PAID, one PARTIAL, and one DRAFT invoice
            invoice_date = date.today() - timedelta(days=3)
            
            # Invoice 1: PAID
            invoice_1 = Invoice(
                invoice_no="INV-2026-0001",
                dealer_id=dealers[0].id,
                dsr_id=dsrs[0].id,
                shop_id=shops[0].id,
                date=invoice_date,
                subtotal=Decimal("7920.00"),
                vat_amount=Decimal("1188.00"),
                discount=Decimal("200.00"),
                grand_total=Decimal("8908.00"),
                paid_amount=Decimal("8908.00"),
                status=InvoiceStatus.PAID,
                notes="Standard wholesale order.",
                created_by=admin_id
            )
            session.add(invoice_1)
            await session.flush()

            item_1_1 = InvoiceItem(
                invoice_id=invoice_1.id,
                product_id=products[0].id,
                qty_carton=10,
                qty_pcs=0,
                total_pieces=240,
                unit_price=products[0].sell_price,
                vat_rate=products[0].vat_rate,
                vat_amount=Decimal("648.00"),
                discount=Decimal("0.00"),
                line_total=Decimal("4968.00")
            )
            item_1_2 = InvoiceItem(
                invoice_id=invoice_1.id,
                product_id=products[2].id,
                qty_carton=5,
                qty_pcs=0,
                total_pieces=300,
                unit_price=products[2].sell_price,
                vat_rate=products[2].vat_rate,
                vat_amount=Decimal("135.00"),
                discount=Decimal("0.00"),
                line_total=Decimal("2835.00")
            )
            session.add_all([item_1_1, item_1_2])

            # Deduct stock movements for the sales
            sm_1_1 = StockMovement(
                product_id=products[0].id,
                movement_type=MovementType.SALE,
                qty_pieces=240,
                unit_price=products[0].sell_price,
                movement_date=invoice_date,
                reference_id=invoice_1.id,
                reference_type="INVOICE",
                created_by=admin_id
            )
            sm_1_2 = StockMovement(
                product_id=products[2].id,
                movement_type=MovementType.SALE,
                qty_pieces=300,
                unit_price=products[2].sell_price,
                movement_date=invoice_date,
                reference_id=invoice_1.id,
                reference_type="INVOICE",
                created_by=admin_id
            )
            session.add_all([sm_1_1, sm_1_2])

            # Seed Collection for Invoice 1
            col_1 = Collection(
                invoice_id=invoice_1.id,
                dealer_id=dealers[0].id,
                dsr_id=dsrs[0].id,
                amount=Decimal("8908.00"),
                payment_method=PaymentMethod.CASH,
                reference_no="CASH-REC-001",
                notes="Collected full amount",
                collected_at=datetime.utcnow() - timedelta(days=3),
                created_by=admin_id
            )
            session.add(col_1)

            # Invoice 2: PARTIAL
            invoice_2 = Invoice(
                invoice_no="INV-2026-0002",
                dealer_id=dealers[1].id,
                dsr_id=dsrs[1].id,
                shop_id=shops[2].id,
                date=invoice_date + timedelta(days=1),
                subtotal=Decimal("18000.00"),
                vat_amount=Decimal("2700.00"),
                discount=Decimal("500.00"),
                grand_total=Decimal("20200.00"),
                paid_amount=Decimal("10000.00"),
                status=InvoiceStatus.PARTIAL,
                notes="Partial payment received.",
                created_by=admin_id
            )
            session.add(invoice_2)
            await session.flush()

            item_2_1 = InvoiceItem(
                invoice_id=invoice_2.id,
                product_id=products[1].id,
                qty_carton=20,
                qty_pcs=8,
                total_pieces=488,
                unit_price=products[1].sell_price,
                vat_rate=products[1].vat_rate,
                vat_amount=Decimal("2635.20"),
                discount=Decimal("0.00"),
                line_total=Decimal("20203.20")
            )
            session.add(item_2_1)

            # Deduct stock movements for the sales
            sm_2_1 = StockMovement(
                product_id=products[1].id,
                movement_type=MovementType.SALE,
                qty_pieces=488,
                unit_price=products[1].sell_price,
                movement_date=invoice_date + timedelta(days=1),
                reference_id=invoice_2.id,
                reference_type="INVOICE",
                created_by=admin_id
            )
            session.add(sm_2_1)

            # Seed Collection for Invoice 2
            col_2 = Collection(
                invoice_id=invoice_2.id,
                dealer_id=dealers[1].id,
                dsr_id=dsrs[1].id,
                amount=Decimal("10000.00"),
                payment_method=PaymentMethod.BKASH,
                reference_no="TXN-BK-9912234",
                notes="Partial payment via bKash",
                collected_at=datetime.utcnow() - timedelta(days=2),
                created_by=admin_id
            )
            session.add(col_2)

            # Invoice 3: DRAFT
            invoice_3 = Invoice(
                invoice_no="INV-2026-0003",
                dealer_id=dealers[0].id,
                dsr_id=dsrs[0].id,
                shop_id=shops[1].id,
                date=date.today(),
                subtotal=Decimal("2208.00"),
                vat_amount=Decimal("331.20"),
                discount=Decimal("0.00"),
                grand_total=Decimal("2539.20"),
                paid_amount=Decimal("0.00"),
                status=InvoiceStatus.DRAFT,
                notes="Draft order, not confirmed yet.",
                created_by=admin_id
            )
            session.add(invoice_3)
            await session.flush()

            item_3_1 = InvoiceItem(
                invoice_id=invoice_3.id,
                product_id=products[3].id,
                qty_carton=1,
                qty_pcs=0,
                total_pieces=48,
                unit_price=products[3].sell_price,
                vat_rate=products[3].vat_rate,
                vat_amount=Decimal("331.20"),
                discount=Decimal("0.00"),
                line_total=Decimal("2539.20")
            )
            session.add(item_3_1)
            # NO stock movement or collection since it's a DRAFT!

            print(f"Seeded {len([invoice_1, invoice_2, invoice_3])} Invoices & Items")

    await engine.dispose()
    print("\nDemo Seeding Complete!")

if __name__ == "__main__":
    asyncio.run(seed_demo())
