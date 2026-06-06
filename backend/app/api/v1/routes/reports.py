from datetime import date
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_permission
from app.schemas.common import SuccessResponse
from app.services import report_service
from app.utils.excel import generate_excel_from_dict_list

router = APIRouter(prefix="/reports", tags=["reports"])

def _handle_response(data: list[dict], export: bool, filename: str):
    if export:
        excel_file = generate_excel_from_dict_list(data, sheet_name=filename)
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    return SuccessResponse(data=data)


@router.get("/daybook")
async def get_daybook(
    report_date: date = Query(default_factory=date.today),
    export: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("reports", "view")),
):
    data = await report_service.get_daybook(db, report_date)
    if export:
        # For Excel, we'll export the transactions list. 
        # A true daybook might need a custom layout, but tabular transactions work.
        return _handle_response(data["transactions"], export, f"Daybook_{report_date}")
    return SuccessResponse(data=data)


@router.get("/sales")
async def get_sales(
    date_from: date = Query(...),
    date_to: date = Query(...),
    dsr_id: Optional[uuid.UUID] = Query(default=None),
    dealer_id: Optional[uuid.UUID] = Query(default=None),
    export: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("reports", "view")),
):
    data = await report_service.get_sales_report(
        db, date_from, date_to, dsr_id, dealer_id
    )
    return _handle_response(data, export, f"Sales_Report_{date_from}_to_{date_to}")


@router.get("/product-sales")
async def get_product_sales(
    date_from: date = Query(...),
    date_to: date = Query(...),
    export: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("reports", "view")),
):
    data = await report_service.get_product_sales_report(db, date_from, date_to)
    return _handle_response(data, export, f"Product_Sales_{date_from}_to_{date_to}")


@router.get("/profit")
async def get_profit(
    date_from: date = Query(...),
    date_to: date = Query(...),
    export: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("reports", "view")),
):
    data = await report_service.get_profit_report(db, date_from, date_to)
    return _handle_response(data, export, f"Profit_Report_{date_from}_to_{date_to}")


@router.get("/vat")
async def get_vat(
    date_from: date = Query(...),
    date_to: date = Query(...),
    export: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("reports", "view")),
):
    data = await report_service.get_vat_report(db, date_from, date_to)
    return _handle_response(data, export, f"VAT_Report_{date_from}_to_{date_to}")


@router.get("/stock-movement/{product_id}")
async def get_stock_movement(
    product_id: uuid.UUID = Path(...),
    export: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("reports", "view")),
):
    data = await report_service.get_stock_movement_report(db, product_id)
    return _handle_response(data, export, f"Stock_Movement_{product_id}")
