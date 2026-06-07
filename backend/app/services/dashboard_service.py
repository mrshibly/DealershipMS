import calendar
import uuid
from datetime import date, timedelta
from typing import Any
from decimal import Decimal

from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice, InvoiceStatus, InvoiceItem
from app.models.collection import Collection
from app.models.expense import Expense
from app.models.product import Product
from app.models.stock_movement import StockMovement, MovementType, INWARD_TYPES, OUTWARD_TYPES
from app.models.purchase import Purchase
from app.models.category import Category
from app.models.target import Target
from app.models.account import Account, AccountType
from app.services.account_service import compute_balance

async def get_daily_snapshot(
    db: AsyncSession,
    date_from: date,
    date_to: date
) -> dict[str, Any]:
    # 1. Net Sales
    sales_result = await db.execute(
        select(func.sum(Invoice.grand_total)).where(
            Invoice.date >= date_from,
            Invoice.date <= date_to,
            Invoice.is_deleted.is_(False),
            Invoice.status != InvoiceStatus.VOID
        )
    )
    net_sales = sales_result.scalar() or Decimal("0.00")

    # 2. Net Purchase
    purchase_result = await db.execute(
        select(func.sum(Purchase.total)).where(
            Purchase.purchase_date >= date_from,
            Purchase.purchase_date <= date_to,
            Purchase.is_deleted.is_(False)
        )
    )
    net_purchase = purchase_result.scalar() or Decimal("0.00")

    # 3. Current Stock Valuation (based on current stock count and buy price)
    inward_vals = [t.value for t in INWARD_TYPES]
    stock_qty_expr = func.coalesce(func.sum(case(
        (StockMovement.movement_type.in_(inward_vals), StockMovement.qty_pieces),
        else_=-StockMovement.qty_pieces
    )), 0).label("stock_qty")
    
    stock_query = (
        select(Product.buy_price, stock_qty_expr)
        .outerjoin(StockMovement, StockMovement.product_id == Product.id)
        .where(Product.is_deleted.is_(False))
        .group_by(Product.id, Product.buy_price)
    )
    stock_res = await db.execute(stock_query)
    total_stock_value = Decimal("0.00")
    for buy_price, qty in stock_res.all():
        total_stock_value += buy_price * max(0, qty)

    # 4. Profit & Loss: Revenue - COGS - Expenses in the date range
    # Revenue (net of void/deleted invoices)
    revenue = net_sales
    
    # Cost of Goods Sold (COGS)
    cogs_query = (
        select(func.sum(InvoiceItem.total_pieces * Product.buy_price))
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .join(Product, Product.id == InvoiceItem.product_id)
        .where(
            Invoice.date >= date_from,
            Invoice.date <= date_to,
            Invoice.is_deleted.is_(False),
            Invoice.status != InvoiceStatus.VOID,
            InvoiceItem.is_free_item.is_(False)
        )
    )
    cogs_res = await db.execute(cogs_query)
    cogs = cogs_res.scalar() or Decimal("0.00")
    
    # Expenses
    expense_result = await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.date >= date_from,
            Expense.date <= date_to,
            Expense.is_deleted.is_(False)
        )
    )
    expenses = expense_result.scalar() or Decimal("0.00")
    
    profit_loss = revenue - cogs - expenses

    # 5. DSR Sales Due: grand_total - paid_amount (for all valid invoices in the date range)
    due_result = await db.execute(
        select(func.sum(Invoice.grand_total - Invoice.paid_amount)).where(
            Invoice.date >= date_from,
            Invoice.date <= date_to,
            Invoice.is_deleted.is_(False),
            Invoice.status != InvoiceStatus.VOID
        )
    )
    dsr_sales_due = due_result.scalar() or Decimal("0.00")

    # 6. Supplier Due: total - paid (for all valid purchases in the date range)
    supplier_due_result = await db.execute(
        select(func.sum(Purchase.total - Purchase.paid)).where(
            Purchase.purchase_date >= date_from,
            Purchase.purchase_date <= date_to,
            Purchase.is_deleted.is_(False)
        )
    )
    supplier_due = supplier_due_result.scalar() or Decimal("0.00")

    # 7. Cash Balance
    cash_accounts = await db.execute(
        select(Account).where(Account.type == AccountType.CASH, Account.is_active.is_(True), Account.is_deleted.is_(False))
    )
    cash_balance = Decimal("0.00")
    for acc in cash_accounts.scalars().all():
        cash_balance += await compute_balance(db, acc.id)
        
    # 8. Bank & Mobile Bank Balance
    bank_accounts = await db.execute(
        select(Account).where(Account.type.in_([AccountType.BANK, AccountType.MOBILE_BANKING]), Account.is_active.is_(True), Account.is_deleted.is_(False))
    )
    bank_balance = Decimal("0.00")
    for acc in bank_accounts.scalars().all():
        bank_balance += await compute_balance(db, acc.id)

    # 9. Top Selling Products Table (limit 10)
    top_selling_query = (
        select(
            Product.name_en,
            Product.name_bn,
            Product.sku,
            Product.brand,
            Category.name.label("category_name"),
            func.sum(InvoiceItem.total_pieces).label("total_sold"),
            func.sum(InvoiceItem.line_total).label("total_sales")
        )
        .join(InvoiceItem, InvoiceItem.product_id == Product.id)
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .outerjoin(Category, Category.id == Product.category_id)
        .where(
            Product.is_deleted.is_(False),
            Invoice.date >= date_from,
            Invoice.date <= date_to,
            Invoice.is_deleted.is_(False),
            Invoice.status != InvoiceStatus.VOID
        )
        .group_by(Product.id, Category.name)
        .order_by(func.sum(InvoiceItem.line_total).desc())
        .limit(10)
    )
    top_selling_res = await db.execute(top_selling_query)
    top_selling = [
        {
            "product_name": row.name_en,
            "product_name_bn": row.name_bn,
            "sku": row.sku,
            "brand": row.brand or "N/A",
            "category": row.category_name or "N/A",
            "total_sales": float(row.total_sales or 0.0)
        }
        for row in top_selling_res.all()
    ]

    # 10. Stock Alert Lists Table
    stock_alerts_query = (
        select(
            Product.id,
            Product.name_en,
            Product.name_bn,
            Product.sku,
            Product.brand,
            Product.low_stock_threshold,
            Category.name.label("category_name"),
            stock_qty_expr
        )
        .outerjoin(StockMovement, StockMovement.product_id == Product.id)
        .outerjoin(Category, Category.id == Product.category_id)
        .where(Product.is_deleted.is_(False))
        .group_by(Product.id, Category.name)
    )
    stock_alerts_res = await db.execute(stock_alerts_query)
    stock_alerts = []
    for row in stock_alerts_res.all():
        qty = max(0, row.stock_qty)
        if qty <= row.low_stock_threshold:
            stock_alerts.append({
                "product_name": row.name_en,
                "product_name_bn": row.name_bn,
                "sku": row.sku,
                "brand": row.brand or "N/A",
                "category": row.category_name or "N/A",
                "qty": qty,
                "low_stock_threshold": row.low_stock_threshold
            })

    # 11. Actual Sales vs Target Chart
    year = date_to.year
    target_query = (
        select(
            func.extract('month', Target.target_month).label("month"),
            func.sum(Target.target_amount).label("target_sum")
        )
        .where(func.extract('year', Target.target_month) == year)
        .group_by(func.extract('month', Target.target_month))
    )
    target_res = await db.execute(target_query)
    targets_by_month = {int(row.month): float(row.target_sum or 0.0) for row in target_res.all()}
    
    sales_query = (
        select(
            func.extract('month', Invoice.date).label("month"),
            func.sum(Invoice.grand_total).label("sales_sum")
        )
        .where(
            func.extract('year', Invoice.date) == year,
            Invoice.is_deleted.is_(False),
            Invoice.status != InvoiceStatus.VOID
        )
        .group_by(func.extract('month', Invoice.date))
    )
    sales_res = await db.execute(sales_query)
    sales_by_month = {int(row.month): float(row.sales_sum or 0.0) for row in sales_res.all()}
    
    sales_vs_target = []
    for m in range(1, 13):
        sales_vs_target.append({
            "label": calendar.month_abbr[m],
            "actual_sales": sales_by_month.get(m, 0.0),
            "target": targets_by_month.get(m, 0.0)
        })

    return {
        "kpis": {
            "net_sales": float(net_sales),
            "net_purchase": float(net_purchase),
            "current_stock": float(total_stock_value),
            "profit_loss": float(profit_loss),
            "dsr_sales_due": float(dsr_sales_due),
            "supplier_due": float(supplier_due),
            "cash_balance": float(cash_balance),
            "bank_balance": float(bank_balance)
        },
        "top_selling": top_selling,
        "stock_alerts": stock_alerts,
        "sales_vs_target": sales_vs_target
    }

async def get_analytics(db: AsyncSession, period: str = "monthly") -> list[dict[str, Any]]:
    # Keep compatibility with old analytics if needed, but we now return sales_vs_target
    # inside snapshot. We will return an empty list or general data for safety.
    return []
