import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_advisory_api_generate_approve_and_analyze(async_client: AsyncClient):
    # 1. Register & Login as Admin
    await async_client.post("/api/v1/auth/register", json={
        "email": "admin_ai@openquant.internal",
        "password": "AdminAIPass123!",
        "full_name": "Admin AI User",
        "role": "ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "admin_ai@openquant.internal",
        "password": "AdminAIPass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Generate strategy
    gen_payload = {
        "prompt": "Momentum strategy based on EMA cross with stop loss",
        "strategy_name": "AI_EMA_Momentum",
        "strategy_type": "TREND_FOLLOWING",
        "symbols": ["AAPL"],
    }
    res_gen = await async_client.post("/api/v1/ai/generate-strategy", json=gen_payload, headers=headers)
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    assert gen_data["strategy_name"] == "AI_EMA_Momentum"
    assert gen_data["ast_safety_passed"] is True
    assert gen_data["review_status"] == "PENDING_HUMAN_REVIEW"
    generation_id = gen_data["generation_id"]

    # 3. Approve strategy (Human in the loop Rule 3)
    res_appr = await async_client.post(
        f"/api/v1/ai/approve/{generation_id}",
        json={"import_as_draft": True},
        headers=headers,
    )
    assert res_appr.status_code == 200
    appr_data = res_appr.json()
    assert appr_data["review_status"] == "APPROVED_BY_HUMAN"
    assert appr_data["reviewed_by"] is not None

    # 4. Analyze logs
    res_log = await async_client.post("/api/v1/ai/analyze-logs", json={"timeframe_hours": 24}, headers=headers)
    assert res_log.status_code == 200
    log_data = res_log.json()
    assert "health_score" in log_data

    # 5. Explain risk
    risk_payload = {
        "risk_rejection_reason": "Order rejected: Market data staleness exceeded 3000ms threshold",
        "account_id": "acc_main",
        "symbol": "AAPL",
        "attempted_quantity": 10,
    }
    res_risk = await async_client.post("/api/v1/ai/explain-risk", json=risk_payload, headers=headers)
    assert res_risk.status_code == 200
    risk_data = res_risk.json()
    assert "Rule 7" in risk_data["breach_category"]
