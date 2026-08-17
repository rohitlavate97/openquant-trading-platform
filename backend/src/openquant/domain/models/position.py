"""Domain models for position tracking and portfolio state."""

from datetime import datetime, timezone
from enum import StrEnum
from decimal import Decimal
from pydantic import BaseModel, Field


class PositionSide(StrEnum):
    """Direction of the position."""
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


class Position(BaseModel):
    """Domain entity representing an active position."""
    position_id: str
    account_id: str
    strategy_id: str
    broker_id: str
    symbol: str
    side: PositionSide = PositionSide.FLAT
    quantity: Decimal = Decimal("0")
    entry_price: Decimal = Decimal("0")
    current_price: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def market_value(self) -> Decimal:
        """Calculate gross market value of the position."""
        return abs(self.quantity * self.current_price)

    def update_market_price(self, new_price: Decimal) -> None:
        """Update current price and recalculate unrealized PnL."""
        self.current_price = new_price
        self.updated_at = datetime.now(timezone.utc)
        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (new_price - self.entry_price) * self.quantity
        elif self.side == PositionSide.SHORT:
            self.unrealized_pnl = (self.entry_price - new_price) * self.quantity
        else:
            self.unrealized_pnl = Decimal("0")
