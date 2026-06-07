import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models.dsr import DSR

@pytest.mark.asyncio
async def test_targets_e2e(auth_client: AsyncClient, db_session: AsyncSession):
    # Setup DSR
    dsr = DSR(name="DSR 1", phone="01711223344")
    db_session.add(dsr)
    await db_session.commit()
    await db_session.refresh(dsr)

    # 1. Create Target
    payload = {
        "dsr_id": str(dsr.id),
        "target_month": "2023-10-01",
        "target_amount": 10000.0,
        "notes": "Q4 Target"
    }
    
    response = await auth_client.post("/api/v1/targets", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["target_amount"] == 10000.0
    assert data["dsr_id"] == str(dsr.id)

    # 2. List Targets
    response = await auth_client.get("/api/v1/targets?month=2023-10-01")
    assert response.status_code == 200
    data_list = response.json()["data"]
    assert len(data_list) > 0
    assert data_list[0]["target_amount"] == 10000.0
    assert data_list[0]["achieved_amount"] == 0.0 # No invoices yet
