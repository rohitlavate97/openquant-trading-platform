"""Application Service orchestrating Backtest simulations, Walk-Forward Validation, and Stage 2 Promotion."""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any
import random

from openquant.domain.models.strategy import Strategy
from openquant.domain.models.market_data import Candle
from openquant.domain.models.promotion import StrategyPromotionStage
from openquant.domain.models.backtest import (
    BacktestConfig,
    BacktestResult,
    WalkForwardResult,
)
from openquant.domain.ports.backtest_port import IBacktestEngine
from openquant.domain.ports.repositories import IStrategyRepository
from openquant.adapters.backtest.event_driven_engine import event_driven_backtest_engine
from openquant.application.services.strategy_service import StrategyService, strategy_service
from openquant.application.services.audit_service import AuditLogService, audit_log_service

logger = logging.getLogger(__name__)


class BacktestService:
    """Application service for historical simulations and walk-forward efficiency validation."""

    def __init__(
        self,
        engine: IBacktestEngine | None = None,
        strategy_svc: StrategyService | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self._engine: IBacktestEngine = engine or event_driven_backtest_engine
        self._strategy_service: StrategyService = strategy_svc or strategy_service
        self._audit: AuditLogService = audit or audit_log_service
        self._results_cache: dict[str, BacktestResult] = {}
        self._wfv_cache: dict[str, WalkForwardResult] = {}

    def generate_synthetic_candles(
        self,
        symbol: str = "AAPL",
        num_candles: int = 120,
        base_price: float = 180.0,
        start_time: datetime | None = None,
    ) -> list[Candle]:
        """Generate realistic synthetic OHLCV candle dataset for historical simulation."""
        now = start_time or (datetime.now(timezone.utc) - timedelta(minutes=num_candles))
        candles: list[Candle] = []
        current_price = base_price

        for i in range(num_candles):
            t = now + timedelta(minutes=i)
            # Random walk price drift
            pct_change = random.gauss(0.0003, 0.004)
            open_p = current_price
            close_p = open_p * (1.0 + pct_change)
            high_p = max(open_p, close_p) * (1.0 + abs(random.gauss(0.0, 0.002)))
            low_p = min(open_p, close_p) * (1.0 - abs(random.gauss(0.0, 0.002)))
            volume = Decimal(str(random.randint(500, 5000)))

            candles.append(
                Candle(
                    symbol=symbol,
                    timeframe="1m",
                    open=Decimal(str(round(open_p, 4))),
                    high=Decimal(str(round(high_p, 4))),
                    low=Decimal(str(round(low_p, 4))),
                    close=Decimal(str(round(close_p, 4))),
                    volume=volume,
                    timestamp=t,
                )
            )
            current_price = close_p

        return candles

    async def run_backtest(
        self,
        config: BacktestConfig,
        custom_candles: list[Candle] | None = None,
        actor_id: str = "system",
    ) -> BacktestResult:
        """Run event-driven backtesting simulation for a given strategy."""
        strat = await self._strategy_service.get_strategy(config.strategy_id)
        if not strat:
            # Fallback placeholder strategy for direct backtest requests
            strat = Strategy(
                strategy_id=config.strategy_id,
                name="Backtest Target Strategy",
                source_code="# EMAMomentumStrategy\nfast_sma = 0",
                symbols=config.symbols,
            )

        candles = custom_candles
        if not candles or len(candles) < 10:
            candles = self.generate_synthetic_candles(
                symbol=config.symbols[0] if config.symbols else "AAPL",
                num_candles=100,
            )

        result = await self._engine.run_backtest(
            config=config,
            strategy=strat,
            historical_candles=candles,
        )

        self._results_cache[result.backtest_id] = result

        await self._audit.log_event(
            event_type="BACKTEST_RUN",
            actor_id=actor_id,
            entity_type="STRATEGY",
            entity_id=config.strategy_id,
            action="RUN_BACKTEST",
            payload={
                "backtest_id": result.backtest_id,
                "net_profit": str(result.metrics.total_net_profit),
                "sharpe": result.metrics.sharpe_ratio,
                "max_drawdown_pct": result.metrics.max_drawdown_pct,
            },
        )
        return result

    async def run_walk_forward_validation(
        self,
        config: BacktestConfig,
        custom_candles: list[Candle] | None = None,
        num_windows: int = 4,
        train_ratio: float = 0.7,
        actor_id: str = "system",
    ) -> WalkForwardResult:
        """Run multi-window Walk-Forward Optimization & Validation."""
        strat = await self._strategy_service.get_strategy(config.strategy_id)
        if not strat:
            strat = Strategy(
                strategy_id=config.strategy_id,
                name="Backtest Target Strategy",
                source_code="# EMAMomentumStrategy\nfast_sma = 0",
                symbols=config.symbols,
            )

        candles = custom_candles
        if not candles or len(candles) < 20:
            candles = self.generate_synthetic_candles(
                symbol=config.symbols[0] if config.symbols else "AAPL",
                num_candles=160,
            )

        result = await self._engine.run_walk_forward_validation(
            config=config,
            strategy=strat,
            historical_candles=candles,
            num_windows=num_windows,
            train_ratio=train_ratio,
        )

        self._wfv_cache[result.validation_id] = result
        return result

    async def get_backtest_result(self, backtest_id: str) -> BacktestResult | None:
        """Retrieve cached backtest report."""
        return self._results_cache.get(backtest_id)

    async def promote_strategy_to_backtested(
        self,
        strategy_id: str,
        backtest_id: str,
        actor_id: str = "system",
    ) -> bool:
        """Evaluate backtest results and promote strategy to Stage 2 (BACKTESTED)."""
        strat = await self._strategy_service.get_strategy(strategy_id)
        bt_res = self._results_cache.get(backtest_id)
        if not strat or not bt_res:
            return False

        # Promotion Gate Criteria Rule Check
        metrics = bt_res.metrics
        if metrics.total_net_profit > Decimal("0") and metrics.max_drawdown_pct <= 30.0:
            strat.promotion_stage = StrategyPromotionStage.BACKTEST
            await self._audit.log_event(
                event_type="PROMOTION_GATE_ADVANCE",
                actor_id=actor_id,
                entity_type="STRATEGY",
                entity_id=strategy_id,
                action="PROMOTE",
                payload={"target_stage": StrategyPromotionStage.BACKTEST, "backtest_id": backtest_id},
            )
            return True
        return False


# Global singleton backtest service
backtest_service = BacktestService()
