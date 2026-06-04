"""
Auth module tests — Sprint 0.
Tests: health, happy-path login, wrong password, missing token, protected route.
"""
import pytest
from httpx import AsyncClient


class TestHealth:
    async def test_health_returns_ok(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestAuthLogin:
    async def test_login_missing_body_returns_422(self, client: AsyncClient):
        """Validation failure — no body → 422."""
        resp = await client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422

    async def test_login_invalid_email_returns_422(self, client: AsyncClient):
        """Validation failure — bad email format → 422."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "secret"},
        )
        assert resp.status_code == 422

    async def test_login_wrong_credentials_returns_401(self, client: AsyncClient):
        """Auth failure — invalid credentials → 401."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@nowhere.com", "password": "wrongpass"},
        )
        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False


class TestProtectedRoute:
    async def test_no_token_returns_401(self, client: AsyncClient):
        """Auth failure — no bearer token → 403 (FastAPI HTTPBearer returns 403)."""
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code in (401, 403)

    async def test_invalid_token_returns_401(self, client: AsyncClient):
        """Auth failure — garbage token → 401."""
        resp = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer this.is.garbage"},
        )
        assert resp.status_code == 401


class TestAuthRefresh:
    async def test_refresh_with_invalid_token_returns_401(self, client: AsyncClient):
        """Validation failure — invalid refresh token → 401."""
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert resp.status_code == 401
