"""Integration tests for FastAPI health and system metadata endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Verify /api/v1/health returns ready status."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "version" in data
    assert data["kill_switch_active"] is False


@pytest.mark.asyncio
async def test_system_info_endpoint(async_client: AsyncClient):
    """Verify /api/v1/system/info returns configuration & risk parameters."""
    response = await async_client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "risk_engine" in data
    assert "sandbox" in data
    assert data["sandbox"]["strict_allowlist_mode"] is True


@pytest.mark.asyncio
async def test_promotion_stages_endpoint(async_client: AsyncClient):
    """Verify /api/v1/system/promotion-stages returns the full 7-stage promotion lifecycle."""
    response = await async_client.get("/api/v1/system/promotion-stages")
    assert response.status_code == 200
    stages = response.json()
    assert len(stages) == 7
    expected_order = [
        "DRAFT",
        "SANDBOXED_CODE_REVIEW",
        "BACKTEST",
        "WALK_FORWARD_VALIDATION",
        "PAPER_TRADING",
        "HUMAN_APPROVAL",
        "LIVE_TRADING",
    ]
    actual_order = [s["stage"] for s in stages]
    assert actual_order == expected_order
