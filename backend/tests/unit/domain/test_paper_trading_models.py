"""Unit tests for Paper Trading Domain Models and Stage 5 Promotion Gate."""

from decimal import Decimal
from datetime import datetime, timezone
from openquant.domain.models.paper_trading import (
    PaperAccount,
    PaperOrderExecutionConfig,
    PaperTradingSession,
    PaperTradingSessionStatus,
    PaperTradingGateStatus,
)


def test_paper_account_defaults():
    """Verify PaperAccount model defaults and balance tracking."""
    acc = PaperAccount(account_id="acc_paper_1", name="Alpha Test Account")
    assert acc.account_id == "acc_paper_1"
    assert acc.initial_balance == Decimal("100000.00")
    assert acc.current_cash == Decimal("100000.00")
    assert acc.margin_used == Decimal("0.00")
    assert acc.currency == "USD"


def test_paper_trading_session_state():
    """Verify PaperTradingSession tracking and execution parameters."""
    config = PaperOrderExecutionConfig(latency_ms=120, slippage_bps=3.5)
    sess = PaperTradingSession(
        session_id="psess_1",
        strategy_id="strat_ema_1",
        account_id="acc_paper_1",
        status=PaperTradingSessionStatus.ACTIVE,
        execution_config=config,
        symbols=["AAPL", "TSLA"],
    )
    assert sess.session_id == "psess_1"
    assert sess.status == PaperTradingSessionStatus.ACTIVE
    assert sess.execution_config.latency_ms == 120
    assert sess.execution_config.slippage_bps == 3.5


def test_paper_trading_gate_status_evaluation():
    """Verify PaperTradingGateStatus promotion eligibility."""
    status_pass = PaperTradingGateStatus(
        session_id="psess_1",
        strategy_id="strat_1",
        days_active=15,
        required_days=14,
        trades_count=35,
        required_trades=30,
        current_drawdown_pct=4.2,
        max_allowed_drawdown_pct=10.0,
        eligible_for_promotion=True,
        requirements_met=["15 days completed", "35 trades completed", "Drawdown 4.2% <= 10.0%"],
        requirements_pending=[],
    )
    assert status_pass.eligible_for_promotion is True
    assert len(status_pass.requirements_met) == 3
