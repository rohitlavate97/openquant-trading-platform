from decimal import Decimal
from openquant.domain.models.position import PositionSide
from openquant.domain.models.portfolio import (
    AssetAllocationItem,
    PortfolioPerformanceSnapshot,
    PortfolioPosition,
    PortfolioSummary,
)


def test_portfolio_models():
    pos = PortfolioPosition(
        account_id="acc_main",
        symbol="AAPL",
        side=PositionSide.LONG,
        quantity=Decimal("50"),
        avg_entry_price=Decimal("150.00"),
        current_price=Decimal("160.00"),
        market_value=Decimal("8000.00"),
        unrealized_pnl=Decimal("500.00"),
        unrealized_pnl_pct=6.67,
        allocation_pct=25.0,
    )
    assert pos.symbol == "AAPL"
    assert pos.unrealized_pnl == Decimal("500.00")

    alloc = AssetAllocationItem(
        symbol_or_class="AAPL",
        market_value=Decimal("8000.00"),
        percentage=25.0,
    )
    assert alloc.percentage == 25.0

    summary = PortfolioSummary(
        account_id="acc_main",
        total_equity=Decimal("105000.00"),
        cash_balance=Decimal("97000.00"),
        margin_used=Decimal("8000.00"),
        available_margin=Decimal("97000.00"),
        unrealized_pnl=Decimal("500.00"),
        realized_pnl=Decimal("4500.00"),
        daily_pnl=Decimal("500.00"),
        daily_pnl_pct=0.48,
        peak_equity=Decimal("106000.00"),
        current_drawdown_pct=0.94,
        max_drawdown_pct=2.1,
        active_positions_count=1,
    )
    assert summary.total_equity == Decimal("105000.00")
    assert summary.active_positions_count == 1
