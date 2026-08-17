"""Integration tests for Audit Logs API endpoint."""

import pytest
from httpx import AsyncClient
from openquant.application.services.audit_service import audit_log_service


@pytest.mark.asyncio
async def test_audit_logs_endpoint_list_and_filter(async_client: AsyncClient):
    """Verify recording compliance events and querying via API."""
    # 1. Register & Login User
    await async_client.post("/api/v1/auth/register", json={
        "email": "compliance@openquant.org",
        "password": "CompliancePass123!",
        "full_name": "Compliance Officer",
        "role": "ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "compliance@openquant.org",
        "password": "CompliancePass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Log events
    await audit_log_service.log_event(
        event_type="KILL_SWITCH_HALT",
        actor_id="usr_compliance",
        entity_type="SYSTEM",
        entity_id="GLOBAL",
        action="KILL_SWITCH_ON",
        payload={"trigger": "Risk limit breach in account A1"},
        severity="CRITICAL",
    )

    await audit_log_service.log_event(
        event_type="STRATEGY_REVIEW",
        actor_id="usr_compliance",
        entity_type="STRATEGY",
        entity_id="strat_1",
        action="CODE_REVIEW_PASS",
        payload={"score": 100},
        severity="INFO",
    )

    # 3. Query all logs
    res = await async_client.get("/api/v1/audit-logs", headers=headers)
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 2

    # 4. Filter by severity
    crit_res = await async_client.get("/api/v1/audit-logs?severity=CRITICAL", headers=headers)
    assert crit_res.status_code == 200
    crit_logs = crit_res.json()
    assert all(l["severity"] == "CRITICAL" for l in crit_logs)
