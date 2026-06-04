"""
Pytest fixtures — shared across all test modules.
Uses an in-memory SQLite DB for tests (overrides DATABASE_URL).
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
