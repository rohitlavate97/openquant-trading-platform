"""Unit tests for Strategy Domain Models, Parameters, and Signals."""

from decimal import Decimal
from datetime import datetime, timezone
from openquant.domain.models.strategy import (
    Strategy,
    StrategyState,
    StrategyParameter,
    ParameterType,
    StrategySignal,
)
from openquant.domain.models.promotion import StrategyPromotionStage


def test_strategy_parameter_model():
    """Verify StrategyParameter validation and defaults."""
    param = StrategyParameter(
        name="fast_period",
        param_type=ParameterType.INT,
        default_value=5,
        current_value=5,
        min_value=2,
        max_value=100,
        description="Fast EMA Period",
    )
    assert param.name == "fast_period"
    assert param.current_value == 5
    assert param.min_value == 2


def test_strategy_entity_lifecycle():
    """Verify Strategy entity default states and helper methods."""
    strat = Strategy(
        strategy_id="strat_test_1",
        name="Trend Follower",
        source_code="print('running')",
        parameters=[
            StrategyParameter(name="period", default_value=14, current_value=14),
            StrategyParameter(name="multiplier", default_value=2.0, current_value=2.5),
        ],
        symbols=["AAPL", "MSFT"],
    )
    assert strat.state == StrategyState.INITIALIZED
    assert strat.promotion_stage == StrategyPromotionStage.DRAFT
    assert strat.is_active is False

    param_dict = strat.get_parameter_dict()
    assert param_dict == {"period": 14, "multiplier": 2.5}


def test_strategy_signal_factory():
    """Verify StrategySignal fields and constraints."""
    sig = StrategySignal(
        symbol="AAPL",
        signal_type="BUY",
        confidence=0.92,
        suggested_quantity=Decimal("50"),
        suggested_price=Decimal("185.50"),
    )
    assert sig.symbol == "AAPL"
    assert sig.signal_type == "BUY"
    assert sig.confidence == 0.92
    assert sig.suggested_quantity == Decimal("50")
