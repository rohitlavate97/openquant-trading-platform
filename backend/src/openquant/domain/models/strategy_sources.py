"""Domain models for Additional Strategy Sources (TradingView, MetaTrader 5, Structured Sheets)."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class TradingViewAction(StrEnum):
    """Execution action requested via TradingView alert webhook."""
    BUY = "BUY"
    SELL = "SELL"
    CLOSE = "CLOSE"
    CANCEL = "CANCEL"


class TradingViewWebhookPayload(BaseModel):
    """Structure of an incoming TradingView alert payload with cryptographic signature & nonce."""
    strategy_id: str
    account_id: str = "acc_main"
    broker_id: str = "paper_broker"
    ticker: str
    action: TradingViewAction
    contracts: Decimal = Decimal("1.0")
    price: Decimal | None = None
    order_type: str = "MARKET"
    nonce: str
    timestamp: int  # Unix timestamp in seconds
    signature: str | None = None
    passphrase: str | None = None


class TradingViewWebhookResult(BaseModel):
    """Outcome of processing an authenticated TradingView webhook alert."""
    success: bool
    order_id: str | None = None
    message: str
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MT5ConnectionState(StrEnum):
    """ZeroMQ socket connection lifecycle state for MetaTrader 5 Bridge."""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    HEARTBEAT_TIMEOUT = "HEARTBEAT_TIMEOUT"
    ERROR = "ERROR"


class MT5BridgeCommand(BaseModel):
    """Outbound command dispatched from OpenQuant OMS to MetaTrader 5 EA."""
    command_id: str
    action: str  # BUY, SELL, MODIFY, CLOSE, PING
    symbol: str
    volume: Decimal
    price: Decimal | None = None
    sl: Decimal | None = None
    tp: Decimal | None = None
    comment: str = "OpenQuant MT5 Bridge"


class MT5BridgeMessage(BaseModel):
    """Inbound telemetry or trade message received from MetaTrader 5 EA."""
    message_id: str
    ea_id: str
    event_type: str  # HEARTBEAT, TICK, EXECUTION, ERROR
    payload: dict[str, Any] = Field(default_factory=dict)
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MT5BridgeStatus(BaseModel):
    """Telemetry report of the MT5 ZeroMQ bridge health and EA connectivity."""
    state: MT5ConnectionState = MT5ConnectionState.DISCONNECTED
    connected_eas_count: int = 0
    last_heartbeat: datetime | None = None
    messages_processed: int = 0
    latency_ms: float = 0.0


class SheetsSignalType(StrEnum):
    """Trade direction signal from structured Google Sheets or CSV rows."""
    BUY = "BUY"
    SELL = "SELL"
    CLOSE = "CLOSE"


class SheetsStrategyRow(BaseModel):
    """Individual parsed and validated strategy signal row from Google Sheets or CSV."""
    row_index: int
    timestamp: str
    symbol: str
    signal_type: SheetsSignalType
    quantity: Decimal
    limit_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    strategy_tag: str = "sheets_signal"
    is_valid: bool = True
    validation_error: str | None = None


class SheetsParseResult(BaseModel):
    """Outcome of parsing and validating raw CSV or Google Sheet strategy data."""
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    rows: list[SheetsStrategyRow] = Field(default_factory=list)
    parsed_orders: list[dict[str, Any]] = Field(default_factory=list)
