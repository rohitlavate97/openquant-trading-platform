"""Integration tests for Security & Penetration Testing API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_security_audit_report_and_penetration_test_endpoints(async_client: AsyncClient):
    """Verify security audit diagnostics report and live penetration test execution."""
    # 1. Register & Login Super Admin
    await async_client.post("/api/v1/auth/register", json={
        "email": "security.officer@openquant.org",
        "password": "SecAdmin12345!",
        "full_name": "Chief Security Officer",
        "role": "SUPER_ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "security.officer@openquant.org",
        "password": "SecAdmin12345!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Security Audit Report
    report_res = await async_client.get("/api/v1/security/audit-report", headers=headers)
    assert report_res.status_code == 200
    report = report_res.json()
    assert report["overall_status"] in ["CERTIFIED", "VULNERABLE"]
    assert report["total_checks"] >= 5
    assert report["security_score_percent"] == 100.0
    assert any(c["check_id"] == "AST_SANDBOX_DEFENSE" for c in report["checks"])
    assert any(c["check_id"] == "SECRETS_VAULT_AES_PBKDF2" for c in report["checks"])
    assert any(c["check_id"] == "WEBHOOK_REPLAY_HMAC_GUARD" for c in report["checks"])

    # 3. Trigger Live Penetration Test
    pen_res = await async_client.post("/api/v1/security/run-penetration-test", headers=headers)
    assert pen_res.status_code == 200
    pen_data = pen_res.json()
    assert pen_data["passed_checks"] == pen_data["total_checks"]
    assert pen_data["overall_status"] == "CERTIFIED"
