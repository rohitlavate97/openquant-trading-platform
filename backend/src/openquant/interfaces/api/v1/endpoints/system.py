"""System metadata and configuration information endpoints."""

from fastapi import APIRouter
from openquant.application.services.health_service import HealthService
from openquant.domain.models.promotion import StrategyPromotionStage

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/info", summary="System Information")
async def get_system_info() -> dict:
    """Return platform metadata, active limits, and configuration defaults."""
    return HealthService.get_system_info()


@router.get("/promotion-stages", summary="Strategy Promotion Gate Lifecycle")
async def get_promotion_stages() -> list[dict[str, str | int]]:
    """Return the sequential 7-stage promotion lifecycle definition."""
    stages = [
        (StrategyPromotionStage.DRAFT, 1, "Initial strategy definition and parameter setup."),
        (StrategyPromotionStage.SANDBOXED_CODE_REVIEW, 2, "Mandatory AST static analysis and safe sandbox linting."),
        (StrategyPromotionStage.BACKTEST, 3, "Historical simulation against out-of-sample data."),
        (StrategyPromotionStage.WALK_FORWARD_VALIDATION, 4, "Walk-forward stability testing."),
        (StrategyPromotionStage.PAPER_TRADING, 5, "Live paper trading with broker sandbox data."),
        (StrategyPromotionStage.HUMAN_APPROVAL, 6, "Mandatory human sign-off on performance & metrics."),
        (StrategyPromotionStage.LIVE_TRADING, 7, "Live capital execution with small sizing & gradual scale."),
    ]
    return [
        {"stage": stage.value, "step_order": order, "description": desc}
        for stage, order, desc in stages
    ]
