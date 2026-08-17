"""Integration tests for Encrypted Broker Secrets Vault endpoints."""

import pytest
from httpx import AsyncClient
from openquant.adapters.repositories.in_memory_auth_repo import user_repository, credential_vault_repository


@pytest.fixture(autouse=True)
def clean_repos():
    user_repository.clear()
    credential_vault_repository.clear()


@pytest.mark.asyncio
async def test_secrets_vault_permissions_and_masked_lifecycle(async_client: AsyncClient):
    """Verify storing, masking, permission enforcement, and deletion of broker credentials."""
    # 1. Register Admin User (has BROKER_MANAGE permission)
    await async_client.post("/api/v1/auth/register", json={
        "email": "admin@openquant.org",
        "password": "AdminPassword123!",
        "full_name": "OpenQuant Admin",
        "role": "ADMIN",
    })
    admin_login = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@openquant.org",
        "password": "AdminPassword123!",
    })
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Register Viewer User (does NOT have BROKER_MANAGE permission)
    await async_client.post("/api/v1/auth/register", json={
        "email": "viewer@openquant.org",
        "password": "ViewerPassword123!",
        "full_name": "Auditor",
        "role": "VIEWER",
    })
    viewer_login = await async_client.post("/api/v1/auth/login", json={
        "email": "viewer@openquant.org",
        "password": "ViewerPassword123!",
    })
    viewer_token = viewer_login.json()["access_token"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    # 3. Viewer attempts to store broker secrets -> 403 Forbidden
    cred_payload = {
        "broker_id": "zerodha",
        "account_id": "AB1234",
        "credentials": {
            "api_key": "raw_zerodha_api_key_xyz",
            "api_secret": "raw_zerodha_api_secret_secret",
            "totp_secret": "MYSECRETOTP1234",
        },
    }
    forbidden_res = await async_client.post("/api/v1/secrets/broker-credentials", headers=viewer_headers, json=cred_payload)
    assert forbidden_res.status_code == 403

    # 4. Admin stores broker secrets -> 201 Created
    store_res = await async_client.post("/api/v1/secrets/broker-credentials", headers=admin_headers, json=cred_payload)
    assert store_res.status_code == 201
    store_data = store_res.json()
    assert store_data["broker_id"] == "zerodha"

    # 5. Admin lists credentials -> all sensitive values MUST be masked (never plaintext)
    list_res = await async_client.get("/api/v1/secrets/broker-credentials", headers=admin_headers)
    assert list_res.status_code == 200
    creds_list = list_res.json()
    assert len(creds_list) == 1
    zerodha_cred = creds_list[0]
    assert zerodha_cred["broker_id"] == "zerodha"
    # Verify values are masked
    assert "raw_zerodha" not in str(zerodha_cred["masked_fields"])
    assert "••••" in zerodha_cred["masked_fields"]["api_key"]

    # 6. Admin deletes credential
    del_res = await async_client.delete("/api/v1/secrets/broker-credentials/zerodha", headers=admin_headers)
    assert del_res.status_code == 200

    # 7. List is now empty
    empty_res = await async_client.get("/api/v1/secrets/broker-credentials", headers=admin_headers)
    assert empty_res.status_code == 200
    assert len(empty_res.json()) == 0
