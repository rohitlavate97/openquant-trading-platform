"""Unit tests for TradingView webhook adapter with HMAC signature & replay nonce verification."""

import time
import hmac
import hashlib
from decimal import Decimal
import pytest

from datetime import datetime, timezone
from openquant.domain.models.strategy_sources import (
    TradingViewAction,
    TradingViewWebhookPayload,
)
from openquant.domain.models.market_data import Tick
from openquant.adapters.sources.tradingview_webhook import TradingViewWebhookHandler
from openquant.adapters.repositories.in_memory_oms_repo import (
    InMemoryOrderRepository,
    InMemoryPositionRepository,
)
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.adapters.risk.risk_engine import SynchronousRiskEngine
from openquant.adapters.brokers.paper_adapter import PaperBrokerAdapter
from openquant.application.services.order_service import OrderManagementService
from openquant.application.services.risk_service import risk_service
from openquant.application.services.risk_service import RiskService
from openquant.application.services.audit_service import AuditLogService
from openquant.application.services.market_data_service import market_data_service


@pytest.fixture
def tv_setup():
    order_repo = InMemoryOrderRepository()
    pos_repo = InMemoryPositionRepository()
    audit_repo = InMemoryAuditLogRepository()
    audit_svc = AuditLogService(audit_repo)
    oms = OrderManagementService(
        order_repo=order_repo,
        pos_repo=pos_repo,
        mkt_service=market_data_service,
        audit=audit_svc,
    )

    handler = TradingViewWebhookHandler(
        oms=oms,
        audit=audit_svc,
        default_secret="test_tv_secret_123",
        max_clock_skew_seconds=30,
    )
    return handler, oms


@pytest.mark.asyncio
async def test_valid_tradingview_webhook_execution(tv_setup):
    handler, oms = tv_setup
    await risk_service.deactivate_kill_switch()

    now = int(time.time())
    secret = "test_tv_secret_123"
    nonce = "nonce_tv_001"

    # Ingest fresh tick so 3000ms staleness guard passes
    await market_data_service.ingest_tick(
        Tick(symbol="AAPL", exchange="NASDAQ", last_price=Decimal("150.00"), timestamp=datetime.now(timezone.utc))
    )

    # Compute valid HMAC signature
    msg = f"strat_tv:AAPL:BUY:10:{nonce}:{now}"
    signature = hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()

    payload = TradingViewWebhookPayload(
        strategy_id="strat_tv",
        account_id="acc_main",
        ticker="AAPL",
        action=TradingViewAction.BUY,
        contracts=Decimal("10"),
        nonce=nonce,
        timestamp=now,
        signature=signature,
    )

    result = await handler.verify_and_process_webhook(payload, secret_key=secret)
    assert result.success is True
    assert result.order_id is not None
    assert "successfully submitted" in result.message


@pytest.mark.asyncio
async def test_invalid_hmac_signature_rejected(tv_setup):
    handler, _ = tv_setup
    now = int(time.time())
    nonce = "nonce_tv_002"

    payload = TradingViewWebhookPayload(
        strategy_id="strat_tv",
        account_id="acc_main",
        ticker="AAPL",
        action=TradingViewAction.BUY,
        contracts=Decimal("10"),
        nonce=nonce,
        timestamp=now,
        signature="invalid_tampered_signature_hex",
    )

    result = await handler.verify_and_process_webhook(payload, secret_key="test_tv_secret_123")
    assert result.success is False
    assert "Invalid HMAC-SHA256 signature" in result.message


@pytest.mark.asyncio
async def test_replay_attack_rejected(tv_setup):
    handler, _ = tv_setup
    await risk_service.deactivate_kill_switch()

    now = int(time.time())
    secret = "test_tv_secret_123"
    nonce = "nonce_replay_003"

    # Ingest fresh tick so 3000ms staleness guard passes
    await market_data_service.ingest_tick(
        Tick(symbol="MSFT", exchange="NASDAQ", last_price=Decimal("300.00"), timestamp=datetime.now(timezone.utc))
    )

    msg = f"strat_tv:MSFT:BUY:5:{nonce}:{now}"
    signature = hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()

    payload = TradingViewWebhookPayload(
        strategy_id="strat_tv",
        account_id="acc_main",
        ticker="MSFT",
        action=TradingViewAction.BUY,
        contracts=Decimal("5"),
        nonce=nonce,
        timestamp=now,
        signature=signature,
    )

    # First attempt succeeds
    res1 = await handler.verify_and_process_webhook(payload, secret_key=secret)
    assert res1.success is True

    # Replay with same nonce must be rejected
    res2 = await handler.verify_and_process_webhook(payload, secret_key=secret)
    assert res2.success is False
    assert "Replay attack detected" in res2.message


@pytest.mark.asyncio
async def test_clock_skew_expired_timestamp_rejected(tv_setup):
    handler, _ = tv_setup
    expired_time = int(time.time()) - 100  # 100s in past (> 30s max skew)
    nonce = "nonce_old_004"

    payload = TradingViewWebhookPayload(
        strategy_id="strat_tv",
        account_id="acc_main",
        ticker="AAPL",
        action=TradingViewAction.BUY,
        contracts=Decimal("10"),
        nonce=nonce,
        timestamp=expired_time,
        signature="any",
    )

    result = await handler.verify_and_process_webhook(payload, secret_key="test_tv_secret_123")
    assert result.success is False
    assert "Timestamp rejected: clock skew" in result.message
