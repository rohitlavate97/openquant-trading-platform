"""Integration tests for Strategy Execution Sandbox REST API endpoints."""

import pytest
from httpx import AsyncClient
from openquant.adapters.repositories.in_memory_auth_repo import user_repository


@pytest.fixture(autouse=True)
def clean_user_state():
    user_repository.clear()


@pytest.mark.asyncio
async def test_sandbox_api_templates_validate_and_execute(async_client: AsyncClient):
    """Test full sandbox API workflow: templates, validation, and safe isolated execution."""
    # 1. Register & Login Quant Developer
    await async_client.post("/api/v1/auth/register", json={
        "email": "quant_dev@openquant.internal",
        "password": "QuantSecurePass123!",
        "full_name": "Quant Developer",
        "role": "QUANT_DEVELOPER",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "quant_dev@openquant.internal",
        "password": "QuantSecurePass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Strategy Templates
    res_tmpl = await async_client.get("/api/v1/sandbox/templates", headers=headers)
    assert res_tmpl.status_code == 200
    templates = res_tmpl.json()
    assert "momentum" in templates
    assert "mean_reversion" in templates

    # 3. Validate clean template code via AST
    momentum_code = templates["momentum"]["code"]
    res_val = await async_client.post(
        "/api/v1/sandbox/validate",
        json={"source_code": momentum_code},
        headers=headers,
    )
    assert res_val.status_code == 200
    assert res_val.json()["is_safe"] is True

    # 4. Validate malicious code via AST -> must report unsafe
    res_mal = await async_client.post(
        "/api/v1/sandbox/validate",
        json={"source_code": "import subprocess\nsubprocess.run(['ls'])"},
        headers=headers,
    )
    assert res_mal.status_code == 200
    assert res_mal.json()["is_safe"] is False
    assert len(res_mal.json()["violations"]) > 0

    # 5. Execute valid strategy in Sandbox
    res_exec = await async_client.post(
        "/api/v1/sandbox/execute",
        json={
            "source_code": momentum_code,
            "strategy_id": "strat_momentum_live",
            "context": {"prices": [180.0, 182.0, 185.0, 188.0], "symbol": "AAPL"},
            "timeout_seconds": 5,
        },
        headers=headers,
    )
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert exec_data["success"] is True
    assert exec_data["output"]["signal"] in ["BUY", "SELL", "HOLD"]
    assert "Evaluated AAPL" in exec_data["output"]["_logs"]
