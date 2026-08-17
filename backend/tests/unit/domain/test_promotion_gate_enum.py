"""Unit tests for the Strategy Promotion Gate lifecycle."""

from openquant.domain.models.promotion import (
    StrategyEntity,
    StrategyPromotionStage,
    StrategySourceType,
    PromotionCriteria,
)


def test_strategy_promotion_gate_sequential_progression():
    """Verify strategy cannot jump stages forward (e.g., Draft straight to Live)."""
    strategy = StrategyEntity(
        strategy_id="strat_99",
        name="Momentum Breakout",
        source_type=StrategySourceType.PYTHON_CODE,
        author_id="user_1",
    )

    assert strategy.current_stage == StrategyPromotionStage.DRAFT
    assert strategy.is_live_enabled is False

    # Valid next step: SANDBOXED_CODE_REVIEW
    assert strategy.can_transition_to(StrategyPromotionStage.SANDBOXED_CODE_REVIEW) is True

    # Invalid bypass steps:
    assert strategy.can_transition_to(StrategyPromotionStage.BACKTEST) is False
    assert strategy.can_transition_to(StrategyPromotionStage.WALK_FORWARD_VALIDATION) is False
    assert strategy.can_transition_to(StrategyPromotionStage.PAPER_TRADING) is False
    assert strategy.can_transition_to(StrategyPromotionStage.HUMAN_APPROVAL) is False
    assert strategy.can_transition_to(StrategyPromotionStage.LIVE_TRADING) is False


def test_strategy_promotion_demotion_allowed_on_risk_breach():
    """Verify demotion is always permitted to any prior stage for capital safety."""
    strategy = StrategyEntity(
        strategy_id="strat_99",
        name="Momentum Breakout",
        source_type=StrategySourceType.AI_GENERATED,
        author_id="user_1",
        current_stage=StrategyPromotionStage.HUMAN_APPROVAL,
    )

    # Demotions backwards are allowed
    assert strategy.can_transition_to(StrategyPromotionStage.PAPER_TRADING) is True
    assert strategy.can_transition_to(StrategyPromotionStage.BACKTEST) is True
    assert strategy.can_transition_to(StrategyPromotionStage.DRAFT) is True
