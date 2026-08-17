"""Strategy Promotion Gate domain models.

Strict 7-stage lifecycle applying uniformly to every strategy source
(Python, TradingView webhook, MT5, Excel/Sheets, AI-generated code).
No strategy source ever skips any stage.
"""

from datetime import datetime, timezone
from enum import StrEnum
from decimal import Decimal
from pydantic import BaseModel, Field


class StrategyPromotionStage(StrEnum):
    """The 7 mandatory sequential stages of strategy promotion."""
    DRAFT = "DRAFT"
    SANDBOXED_CODE_REVIEW = "SANDBOXED_CODE_REVIEW"
    BACKTEST = "BACKTEST"
    WALK_FORWARD_VALIDATION = "WALK_FORWARD_VALIDATION"
    PAPER_TRADING = "PAPER_TRADING"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    LIVE_TRADING = "LIVE_TRADING"


class StrategySourceType(StrEnum):
    """Normalized source origin of the strategy."""
    PYTHON_CODE = "PYTHON_CODE"
    TRADINGVIEW_WEBHOOK = "TRADINGVIEW_WEBHOOK"
    METATRADER_5 = "METATRADER_5"
    EXCEL_SHEET_RULES = "EXCEL_SHEET_RULES"
    REST_WEBSOCKET_SIGNAL = "REST_WEBSOCKET_SIGNAL"
    AI_GENERATED = "AI_GENERATED"


class PromotionCriteria(BaseModel):
    """Explicit quantitative criteria required for advancing across promotion stages."""
    min_backtest_sharpe: Decimal = Field(default=Decimal("1.2"), description="Minimum annualized Sharpe ratio")
    min_backtest_sortino: Decimal = Field(default=Decimal("1.5"), description="Minimum annualized Sortino ratio")
    max_backtest_drawdown_percent: Decimal = Field(default=Decimal("15.0"), description="Max allowed backtest drawdown %")
    min_walk_forward_efficiency: Decimal = Field(default=Decimal("0.6"), description="Min walk-forward out-of-sample ratio")
    min_paper_trading_days: int = Field(default=14, description="Minimum calendar days of live paper trading")
    min_paper_trading_trades: int = Field(default=30, description="Minimum number of executed paper trades")
    max_paper_trading_drawdown_percent: Decimal = Field(default=Decimal("10.0"), description="Max allowed drawdown during paper")


class PromotionGateRecord(BaseModel):
    """Audit log entry capturing a promotion or automatic demotion event."""
    strategy_id: str
    from_stage: StrategyPromotionStage
    to_stage: StrategyPromotionStage
    approved_by: str | None = None
    reason: str
    metrics: dict[str, str | float | int | bool] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StrategyEntity(BaseModel):
    """Core domain entity representing a trading strategy."""
    strategy_id: str
    name: str
    source_type: StrategySourceType
    current_stage: StrategyPromotionStage = StrategyPromotionStage.DRAFT
    is_live_enabled: bool = False  # Hard safety default: NEVER enabled on creation
    author_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    criteria: PromotionCriteria = Field(default_factory=PromotionCriteria)
    history: list[PromotionGateRecord] = Field(default_factory=list)

    def can_transition_to(self, target_stage: StrategyPromotionStage) -> bool:
        """Verify strict sequential promotion rules."""
        stage_order = [
            StrategyPromotionStage.DRAFT,
            StrategyPromotionStage.SANDBOXED_CODE_REVIEW,
            StrategyPromotionStage.BACKTEST,
            StrategyPromotionStage.WALK_FORWARD_VALIDATION,
            StrategyPromotionStage.PAPER_TRADING,
            StrategyPromotionStage.HUMAN_APPROVAL,
            StrategyPromotionStage.LIVE_TRADING,
        ]
        curr_idx = stage_order.index(self.current_stage)
        target_idx = stage_order.index(target_stage)

        # Allow demotion to any previous stage (or directly back to Draft / Paper Trading on risk breach)
        if target_idx < curr_idx:
            return True

        # Strict forward progression by exactly 1 stage at a time
        return target_idx == curr_idx + 1
