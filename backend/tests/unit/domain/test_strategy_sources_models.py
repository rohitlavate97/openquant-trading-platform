"""Unit tests for Strategy Sources domain models."""

from decimal import Decimal
from openquant.domain.models.strategy_sources import (
    TradingViewAction,
    TradingViewWebhookPayload,
    TradingViewWebhookResult,
    MT5BridgeCommand,
    MT5BridgeMessage,
    MT5BridgeStatus,
    MT5ConnectionState,
    SheetsSignalType,
    SheetsStrategyRow,
    SheetsParseResult,
)


def test_tradingview_models():
    payload = TradingViewWebhookPayload(
        strategy_id="tv_strat_1",
        account_id="acc_main",
        ticker="AAPL",
        action=TradingViewAction.BUY,
        contracts=Decimal("10"),
        nonce="nonce_123",
        timestamp=1700000000,
    )
    assert payload.ticker == "AAPL"
    assert payload.action == TradingViewAction.BUY

    res = TradingViewWebhookResult(success=True, order_id="ord_1", message="Success")
    assert res.success is True
    assert res.order_id == "ord_1"


def test_mt5_models():
    cmd = MT5BridgeCommand(
        command_id="cmd_1",
        action="BUY",
        symbol="EURUSD",
        volume=Decimal("0.1"),
    )
    assert cmd.symbol == "EURUSD"

    status = MT5BridgeStatus(state=MT5ConnectionState.CONNECTED, connected_eas_count=1)
    assert status.state == MT5ConnectionState.CONNECTED
    assert status.connected_eas_count == 1


def test_sheets_models():
    row = SheetsStrategyRow(
        row_index=1,
        timestamp="2026-08-17T12:00:00Z",
        symbol="TSLA",
        signal_type=SheetsSignalType.BUY,
        quantity=Decimal("50"),
        is_valid=True,
    )
    assert row.symbol == "TSLA"
    assert row.quantity == Decimal("50")

    result = SheetsParseResult(
        total_rows=1,
        valid_rows_count=1,
        invalid_rows_count=0,
        rows=[row],
    )
    assert result.total_rows == 1
    assert result.valid_rows_count == 1
