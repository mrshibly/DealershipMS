from datetime import date, timedelta
from typing import Any
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice, InvoiceStatus
from app.models.collection import Collection
from app.models.expense import Expense
from app.models.product import Product
from app.models.stock_movement import StockMovement
from app.models.dealer import Dealer

async def get_daily_snapshot(db: AsyncSession, day: date) -> dict[str, Any]:
    # 1. Today's Sales
    sales_result = await db.execute(
        select(func.sum(Invoice.grand_total)).where(
            Invoice.date == day,
            Invoice.is_deleted.is_(False),
            Invoice.status != InvoiceStatus.VOID
        )
    )
    today_sales = sales_result.scalar() or Decimal("0.00")

    # 2. Today's Collections
    col_result = await db.execute(
        select(func.sum(Collection.amount)).where(
            Collection.date == day,
            Collection.is_deleted.is_(False)
        )
    )
    today_collections = col_result.scalar() or Decimal("0.00")

    # 3. Total Outstanding Due (Across all dealers)
    due_result = await db.execute(
        select(func.sum(Dealer.current_balance)).where(
            Dealer.is_deleted.is_(False),
            Dealer.current_balance > 0
        )
    )
    total_due = due_result.scalar() or Decimal("0.00")

    # 4. Total Stock Value (Base price * current stock)
    # We sum the quantity of all active products and multiply by their price.
    stock_value_result = await db.execute(
        select(func.sum(Product.price * Product.stock_pcs)).where(
            Product.is_deleted.is_(False)
        )
    )
    total_stock_value = stock_value_result.scalar() or Decimal("0.00")

    return {
        "today_sales": float(today_sales),
        "today_collections": float(today_collections),
        "total_due": float(total_due),
        "total_stock_value": float(total_stock_value)
    }

async def get_analytics(db: AsyncSession, period: str = "monthly") -> list[dict[str, Any]]:
    """
    Returns time-series data for Recharts.
    If period == "monthly", returns the last 30 days.
    If period == "yearly", returns the last 12 months.
    """
    data = []
    today = date.today()

    if period == "monthly":
        # Last 30 days
        start_date = today - timedelta(days=29)
        
        # We query all sales and expenses in this range and group them by day in Python
        # to ensure days with 0 sales/expenses are still included in the chart.
        
        sales_result = await db.execute(
            select(Invoice.date, func.sum(Invoice.grand_total)).where(
                Invoice.date >= start_date,
                Invoice.date <= today,
                Invoice.is_deleted.is_(False),
                Invoice.status != InvoiceStatus.VOID
            ).group_by(Invoice.date)
        )
        sales_map = {row[0]: float(row[1]) for row in sales_result.all()}

        expense_result = await db.execute(
            select(Expense.date, func.sum(Expense.amount)).where(
                Expense.date >= start_date,
                Expense.date <= today,
                Expense.is_deleted.is_(False)
            ).group_by(Expense.date)
        )
        expense_map = {row[0]: float(row[1]) for row in expense_result.all()}

        for i in range(30):
            current_day = start_date + timedelta(days=i)
            data.append({
                "label": current_day.strftime("%b %d"),
                "sales": sales_map.get(current_day, 0.0),
                "expenses": expense_map.get(current_day, 0.0)
            })

    elif period == "yearly":
        # Last 12 months (grouped by month)
        # For simplicity, we just aggregate in Python by reading the last 365 days
        start_date = today - timedelta(days=365)
        
        sales_result = await db.execute(
            select(Invoice.date, func.sum(Invoice.grand_total)).where(
                Invoice.date >= start_date,
                Invoice.date <= today,
                Invoice.is_deleted.is_(False),
                Invoice.status != InvoiceStatus.VOID
            ).group_by(Invoice.date)
        )
        
        expense_result = await db.execute(
            select(Expense.date, func.sum(Expense.amount)).where(
                Expense.date >= start_date,
                Expense.date <= today,
                Expense.is_deleted.is_(False)
            ).group_by(Expense.date)
        )

        # Aggregate by Year-Month
        monthly_data = {}
        for row in sales_result.all():
            ym = row[0].strftime("%b %Y")
            if ym not in monthly_data:
                monthly_data[ym] = {"sales": 0.0, "expenses": 0.0}
            monthly_data[ym]["sales"] += float(row[1])
            
        for row in expense_result.all():
            ym = row[0].strftime("%b %Y")
            if ym not in monthly_data:
                monthly_data[ym] = {"sales": 0.0, "expenses": 0.0}
            monthly_data[ym]["expenses"] += float(row[1])

        # Generate the last 12 months in order
        for i in range(11, -1, -1):
            target_date = today.replace(day=1) - timedelta(days=i*30)
            # A little hacky, but robust enough for a quick 12-month loop
            # Better way:
            y = today.year
            m = today.month - i
            if m <= 0:
                m += 12
                y -= 1
            
            # Format to match our dict keys
            dummy_date = date(y, m, 1)
            ym = dummy_date.strftime("%b %Y")
            
            data.append({
                "label": dummy_date.strftime("%b"),
                "sales": monthly_data.get(ym, {}).get("sales", 0.0),
                "expenses": monthly_data.get(ym, {}).get("expenses", 0.0)
            })

    return data
