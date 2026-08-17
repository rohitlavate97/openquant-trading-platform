"""Integration tests for Broker Adapters REST API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_broker_adapters_api_lifecycle(async_client: AsyncClient):
    """Verify listing adapters, connecting, querying funds, and certifying all 5 adapters via API."""
    # 1. Register & Login Super Admin
    await async_client.post("/api/v1/auth/register", json={
        "email": "admin.broker@openquant.org",
        "password": "SuperAdminPass123!",
        "full_name": "Broker Admin",
        "role": "SUPER_ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "admin.broker@openquant.org",
        "password": "SuperAdminPass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. List registered adapters
    res = await async_client.get("/api/v1/brokers", headers=headers)
    assert res.status_code == 200
    adapters = res.json()
    assert len(adapters) >= 5
    adapter_ids = [a["adapter_id"] for a in adapters]
    assert "paper_broker" in adapter_ids
    assert "zerodha" in adapter_ids
    assert "interactive_brokers" in adapter_ids
    assert "angel_one" in adapter_ids
    assert "binance_crypto" in adapter_ids

    # 3. Connect Paper Broker
    conn_res = await async_client.post("/api/v1/brokers/paper_broker/connect", headers=headers)
    assert conn_res.status_code == 200
    assert conn_res.json()["connected"] is True

    # 4. Query funds
    funds_res = await async_client.get("/api/v1/brokers/paper_broker/funds", headers=headers)
    assert funds_res.status_code == 200
    funds = funds_res.json()
    assert float(funds["available_cash"]) > 0

    # 5. Run Certification Audit on all adapters
    for ad_id in ["zerodha", "interactive_brokers", "angel_one", "binance_crypto"]:
        cert_res = await async_client.post(f"/api/v1/brokers/{ad_id}/certify", headers=headers)
        assert cert_res.status_code == 200
        audit_report = cert_res.json()
        assert audit_report["is_certified"] is True
        assert audit_report["live_trading_eligible"] is True
        assert len(audit_report["checks"]) == 5
