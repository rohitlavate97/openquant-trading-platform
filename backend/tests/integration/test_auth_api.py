"""Integration tests for Authentication API endpoints."""

import pytest
from httpx import AsyncClient
from openquant.adapters.repositories.in_memory_auth_repo import user_repository


@pytest.fixture(autouse=True)
def clean_user_repo():
    """Reset repository before each test."""
    user_repository.clear()


@pytest.mark.asyncio
async def test_auth_register_and_login_flow(async_client: AsyncClient):
    """Verify complete registration, login, profile inspection, and token refresh flow."""
    # 1. Register
    reg_payload = {
        "email": "lead.trader@openquant.org",
        "password": "StrongPassword123!",
        "full_name": "Lead Trader",
        "role": "TRADER",
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["user"]["email"] == "lead.trader@openquant.org"

    # Duplicate registration rejection
    dup_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 409

    # 2. Login
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "lead.trader@openquant.org",
        "password": "StrongPassword123!",
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # 3. Access Protected /me endpoint with Bearer Token
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "lead.trader@openquant.org"
    assert "KILL_SWITCH_TRIGGER" in me_data["permissions"]

    # 4. Refresh Token Exchange
    ref_res = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    assert "access_token" in ref_res.json()


@pytest.mark.asyncio
async def test_auth_invalid_credentials_rejected(async_client: AsyncClient):
    """Verify invalid password returns 401."""
    # Register user
    await async_client.post("/api/v1/auth/register", json={
        "email": "test@openquant.org",
        "password": "CorrectPassword123!",
        "full_name": "Test User",
        "role": "TRADER",
    })

    # Wrong password
    bad_login = await async_client.post("/api/v1/auth/login", json={
        "email": "test@openquant.org",
        "password": "WrongPassword!",
    })
    assert bad_login.status_code == 401
