"""Integration tests for Programmatic API Keys endpoints."""

import pytest
from httpx import AsyncClient
from openquant.adapters.repositories.in_memory_auth_repo import user_repository, api_key_repository


@pytest.fixture(autouse=True)
def clean_repos():
    user_repository.clear()
    api_key_repository.clear()


@pytest.mark.asyncio
async def test_api_keys_crud_and_authentication(async_client: AsyncClient):
    """Verify creating, listing, authenticating via X-API-Key, and revoking API keys."""
    # 1. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "botdev@openquant.org",
        "password": "BotPassword123!",
        "full_name": "Bot Developer",
        "role": "QUANT_DEVELOPER",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "botdev@openquant.org",
        "password": "BotPassword123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create API Key
    create_res = await async_client.post(
        "/api/v1/api-keys",
        headers=headers,
        json={
            "name": "Production HFT Key",
            "permissions": ["STRATEGY_CREATE", "READ_ONLY"],
        },
    )
    assert create_res.status_code == 201
    key_data = create_res.json()
    assert "raw_api_key" in key_data
    raw_api_key = key_data["raw_api_key"]
    key_id = key_data["key_id"]

    # 3. List API Keys
    list_res = await async_client.get("/api/v1/api-keys", headers=headers)
    assert list_res.status_code == 200
    keys_list = list_res.json()
    assert len(keys_list) == 1
    assert keys_list[0]["key_id"] == key_id

    # 4. Use X-API-Key to authenticate against protected /me endpoint
    api_key_headers = {"X-API-Key": raw_api_key}
    me_res = await async_client.get("/api/v1/auth/me", headers=api_key_headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "botdev@openquant.org"

    # 5. Revoke API Key
    del_res = await async_client.delete(f"/api/v1/api-keys/{key_id}", headers=headers)
    assert del_res.status_code == 200

    # 6. Authenticating with revoked key fails
    revoked_me = await async_client.get("/api/v1/auth/me", headers=api_key_headers)
    assert revoked_me.status_code == 401
