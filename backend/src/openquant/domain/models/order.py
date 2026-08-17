"""Domain models and value objects for order management."""

from datetime import datetime, timezone
from enum import StrEnum
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class OrderSide(StrEnum):
    """Side of the order."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    """Execution type of the order."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(StrEnum):
    """Lifecycle status of an order."""
    PENDING_RISK_CHECK = "PENDING_RISK_CHECK"
    RISK_REJECTED = "RISK_REJECTED"
    PENDING_SUBMISSION = "PENDING_SUBMISSION"
    SUBMITTED = "SUBMITTED"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TimeInForce(StrEnum):
    """Validity duration for the order."""
    DAY = "DAY"
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


class OrderRequest(BaseModel):
    """Value object representing an inbound order request before OMS and Risk validation."""
    idempotency_key: str = Field(..., min_length=8, description="Client-provided idempotency key")
    strategy_id: str = Field(..., description="ID of the originating strategy")
    account_id: str = Field(..., description="Target trading account identifier")
    broker_id: str = Field(..., description="Target broker adapter identifier")
    symbol: str = Field(..., min_length=1, description="Trading symbol / ticker")
    side: OrderSide
    order_type: OrderType
    quantity: Decimal = Field(..., gt=0, description="Quantity to execute")
    price: Decimal | None = Field(default=None, ge=0, description="Price for LIMIT or STOP_LIMIT orders")
    stop_price: Decimal | None = Field(default=None, ge=0, description="Trigger price for STOP or STOP_LIMIT")
    time_in_force: TimeInForce = TimeInForce.DAY
    tag: str | None = None

    @field_validator("price")
    @classmethod
    def validate_price_for_order_type(cls, v: Decimal | None, info) -> Decimal | None:
        """Ensure LIMIT orders specify a positive price."""
        order_type = info.data.get("order_type")
        if order_type in (OrderType.LIMIT, OrderType.STOP_LIMIT) and (v is None or v <= 0):
            raise ValueError(f"Order type {order_type} requires a positive price")
        return v


class Order(BaseModel):
    """Domain Entity representing an order in the OMS."""
    order_id: str = Field(..., description="Internal unique OpenQuant order UUID")
    idempotency_key: str = Field(..., description="Idempotency key guaranteed unique per account")
    strategy_id: str
    account_id: str
    broker_id: str
    broker_order_id: str | None = None
    symbol: str
    side: OrderSide
    order_type: OrderType
    status: OrderStatus = OrderStatus.PENDING_RISK_CHECK
    quantity: Decimal
    filled_quantity: Decimal = Decimal("0")
    price: Decimal | None = None
    stop_price: Decimal | None = None
    average_fill_price: Decimal | None = None
    time_in_force: TimeInForce = TimeInForce.DAY
    rejection_reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tag: str | None = None

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate unfilled quantity remaining on this order."""
        return max(Decimal("0"), self.quantity - self.filled_quantity)

    @property
    def is_terminal(self) -> bool:
        """Check if order has reached a terminal, immutable lifecycle state."""
        return self.status in (
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.RISK_REJECTED,
            OrderStatus.EXPIRED,
        )


class OrderExecutionReport(BaseModel):
    """Execution update emitted by broker adapter or simulated execution engine."""
    order_id: str
    broker_order_id: str
    execution_id: str
    status: OrderStatus
    last_filled_quantity: Decimal
    last_filled_price: Decimal
    cumulative_filled_quantity: Decimal
    average_price: Decimal
    commission: Decimal = Decimal("0")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_broker_response: dict | None = None
