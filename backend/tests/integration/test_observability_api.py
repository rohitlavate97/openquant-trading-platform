"""Integration tests for Observability, Prometheus /metrics endpoint, and Grafana dashboards."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_prometheus_metrics_and_correlation_id(async_client: AsyncClient):
    """Verify Prometheus scrape endpoint and correlation ID propagation."""
    # 1. Request /metrics endpoint
    res = await async_client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers["content-type"]
    text = res.text
    assert "# HELP openquant_orders_total" in text
    assert "# HELP openquant_kill_switch_active" in text

    # 2. Verify X-Correlation-ID header injection
    assert "x-correlation-id" in res.headers
    cid = res.headers["x-correlation-id"]
    assert cid.startswith("cid_")


@pytest.mark.asyncio
async def test_observability_api_endpoints(async_client: AsyncClient):
    """Verify JSON summary, traces, and Grafana dashboard templates."""
    # 1. Register & Login Super Admin
    await async_client.post("/api/v1/auth/register", json={
        "email": "metrics.admin@openquant.org",
        "password": "MetricsAdmin123!",
        "full_name": "Metrics Admin",
        "role": "SUPER_ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "metrics.admin@openquant.org",
        "password": "MetricsAdmin123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Telemetry Summary
    summary_res = await async_client.get("/api/v1/observability/summary", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert "total_orders_placed" in summary
    assert "total_risk_checks_evaluated" in summary

    # 3. Get Traces
    traces_res = await async_client.get("/api/v1/observability/traces", headers=headers)
    assert traces_res.status_code == 200
    traces = traces_res.json()
    assert isinstance(traces, list)

    # 4. Get Grafana Dashboards
    dash_res = await async_client.get("/api/v1/observability/dashboards", headers=headers)
    assert dash_res.status_code == 200
    dashboards = dash_res.json()
    assert len(dashboards) >= 3
    assert any(d["id"] == "openquant-trading-ops" for d in dashboards)
