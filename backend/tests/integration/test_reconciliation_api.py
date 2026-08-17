"""Integration tests for State Reconciliation REST API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_reconciliation_api_endpoints(async_client: AsyncClient):
    """Test reconciliation run, report listing, detailed report, and sync endpoints."""
    # 1. Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "recon_admin@openquant.internal",
        "password": "ReconSecurePass123!",
        "full_name": "Recon Admin",
        "role": "SUPER_ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "recon_admin@openquant.internal",
        "password": "ReconSecurePass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Run global reconciliation
    run_all_res = await async_client.post("/api/v1/reconciliation/run", headers=headers)
    assert run_all_res.status_code == 200
    assert len(run_all_res.json()) >= 1

    # 3. Run specific account reconciliation
    run_acc_res = await async_client.post("/api/v1/reconciliation/accounts/acc_main/run", headers=headers)
    assert run_acc_res.status_code == 200
    report_id = run_acc_res.json()["report_id"]
    assert "status" in run_acc_res.json()

    # 4. List reports
    list_res = await async_client.get("/api/v1/reconciliation/reports", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 5. Get report details
    rep_res = await async_client.get(f"/api/v1/reconciliation/reports/{report_id}", headers=headers)
    assert rep_res.status_code == 200
    assert rep_res.json()["report_id"] == report_id

    # 6. Force sync
    sync_res = await async_client.post("/api/v1/reconciliation/accounts/acc_main/sync", headers=headers)
    assert sync_res.status_code == 200
