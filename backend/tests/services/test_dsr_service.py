import pytest
import uuid
from decimal import Decimal
from datetime import date

from app.models.route import Route
from app.models.dsr import DSR
from app.models.invoice import Invoice, InvoiceStatus
from app.schemas.dsr import DSRCreate, DSRUpdate
from app.services.dsr_service import (
    list_dsrs,
    get_dsr,
    create_dsr,
    update_dsr,
    delete_dsr,
)
from app.services.dsr_ledger_service import get_dsr_ledger

@pytest.mark.asyncio
async def test_dsr_crud_and_ledger(db_session):
    user_id = uuid.uuid4()
    
    # Setup Route
    route = Route(name="Route North", area="Dhaka")
    db_session.add(route)
    await db_session.flush()

    # 1. Create DSR
    dsr_data = DSRCreate(
        name="DSR North",
        phone="01799887766",
        nid="123456789",
        route_id=route.id,
        commission_rate=Decimal("2.50"),
        is_active=True
    )
    
    dsr = await create_dsr(db_session, dsr_data, user_id)
    assert dsr.name == "DSR North"
    assert dsr.phone == "01799887766"
    assert dsr.route_name == "Route North"

    # Attempt to create DSR with same phone should fail
    with pytest.raises(ValueError):
        await create_dsr(db_session, dsr_data, user_id)

    # 2. Get DSR
    dsr_id = dsr.id
    dsr_db = await get_dsr(db_session, dsr_id)
    assert dsr_db is not None
    assert dsr_db.name == "DSR North"

    # 3. List DSRs
    dsrs, total = await list_dsrs(db_session, search="North")
    assert total == 1
    assert dsrs[0].name == "DSR North"

    # 4. Update DSR
    update_data = DSRUpdate(
        name="DSR North Updated",
        commission_rate=Decimal("3.00")
    )
    updated = await update_dsr(db_session, dsr_id, update_data)
    assert updated.name == "DSR North Updated"
    assert updated.commission_rate == Decimal("3.00")

    # 5. DSR Ledger verification
    # Setup invoice under this DSR
    invoice = Invoice(
        id=uuid.uuid4(),
        invoice_no="INV-2026-DSR",
        date=date.today(),
        subtotal=Decimal("200.00"),
        discount=Decimal("0.00"),
        vat_amount=Decimal("0.00"),
        grand_total=Decimal("200.00"),
        paid_amount=Decimal("50.00"),
        status=InvoiceStatus.CONFIRMED,
        dsr_id=dsr_id,
        created_by=user_id
    )
    db_session.add(invoice)
    await db_session.commit()

    ledger = await get_dsr_ledger(db_session, dsr_id)
    assert ledger is not None
    assert ledger["dsr"]["name"] == "DSR North Updated"
    assert ledger["summary"]["total_sales"] == Decimal("200.00")
    assert ledger["summary"]["total_collected"] == Decimal("50.00")
    assert ledger["summary"]["total_outstanding"] == Decimal("150.00")
    assert ledger["summary"]["commission_earned"] == Decimal("6.00") # 200 * 3.00%
    assert len(ledger["invoices"]) == 1

    # 6. Delete DSR (Soft delete)
    deleted = await delete_dsr(db_session, dsr_id)
    assert deleted is True

    dsr_deleted = await get_dsr(db_session, dsr_id)
    assert dsr_deleted is None

    # Get ledger of non-existent DSR
    non_existent = await get_dsr_ledger(db_session, uuid.uuid4())
    assert non_existent is None
