"""Webhook Replay Attack, HMAC Signature Verification, and Nonce Deduplication Security Tests."""

from decimal import Decimal
import hashlib
import hmac
import time
import uuid
import pytest
from openquant.domain.models.strategy_sources import TradingViewAction, TradingViewWebhookPayload
from openquant.domain.models.market_data import Tick
from openquant.application.services.strategy_sources_service import strategy_sources_service
from openquant.application.services.market_data_service import market_data_service


SECRET_KEY = "openquant_tv_secret_key"


def generate_signed_payload(
    action: TradingViewAction = TradingViewAction.BUY,
    ticker: str = "AAPL",
    contracts: Decimal = Decimal("10.0"),
    timestamp: int | None = None,
    nonce: str | None = None,
    secret: str = SECRET_KEY,
) -> TradingViewWebhookPayload:
    if timestamp is None:
        timestamp = int(time.time())
    if nonce is None:
        nonce = f"nonce_{uuid.uuid4().hex[:12]}"

    message = f"strat_replay_test:{ticker}:{action.value}:{contracts}:{nonce}:{timestamp}"
    sig = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()

    return TradingViewWebhookPayload(
        strategy_id="strat_replay_test",
        account_id="acc_main",
        broker_id="paper_broker",
        ticker=ticker,
        action=action,
        contracts=contracts,
        price=Decimal("150.0"),
        nonce=nonce,
        timestamp=timestamp,
        signature=sig,
    )


@pytest.fixture(autouse=True)
async def seed_market_data():
    await market_data_service.ingest_tick(Tick(
        symbol="AAPL",
        last_price=Decimal("150.00"),
        bid_price=Decimal("149.95"),
        ask_price=Decimal("150.05"),
        volume=Decimal("1000"),
    ))


@pytest.mark.asyncio
async def test_valid_signed_webhook_passes():
    payload = generate_signed_payload()
    result = await strategy_sources_service.handle_tradingview_webhook(payload, secret_key=SECRET_KEY)
    assert result.success is True


@pytest.mark.asyncio
async def test_tampered_payload_signature_rejected():
    payload = generate_signed_payload(action=TradingViewAction.BUY)
    # Tamper action to SELL without recomputing signature
    payload.action = TradingViewAction.SELL
    result = await strategy_sources_service.handle_tradingview_webhook(payload, secret_key=SECRET_KEY)
    assert result.success is False
    assert "Invalid HMAC-SHA256 signature" in result.message


@pytest.mark.asyncio
async def test_expired_timestamp_replay_attack_rejected():
    # 120 seconds in the past (> 60s window)
    expired_ts = int(time.time()) - 120
    payload = generate_signed_payload(timestamp=expired_ts)
    result = await strategy_sources_service.handle_tradingview_webhook(payload, secret_key=SECRET_KEY)
    assert result.success is False
    assert "clock skew" in result.message


@pytest.mark.asyncio
async def test_future_timestamp_spoofing_rejected():
    # 120 seconds in the future
    future_ts = int(time.time()) + 120
    payload = generate_signed_payload(timestamp=future_ts)
    result = await strategy_sources_service.handle_tradingview_webhook(payload, secret_key=SECRET_KEY)
    assert result.success is False
    assert "clock skew" in result.message


@pytest.mark.asyncio
async def test_nonce_replay_attack_rejected():
    fixed_nonce = f"fixed_nonce_{uuid.uuid4().hex[:8]}"
    payload1 = generate_signed_payload(nonce=fixed_nonce)

    # First delivery succeeds
    res1 = await strategy_sources_service.handle_tradingview_webhook(payload1, secret_key=SECRET_KEY)
    assert res1.success is True

    # Replaying the exact same signed payload with same nonce must be blocked
    res2 = await strategy_sources_service.handle_tradingview_webhook(payload1, secret_key=SECRET_KEY)
    assert res2.success is False
    assert "Replay attack detected" in res2.message
