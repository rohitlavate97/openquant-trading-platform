"""Pre-Trade Risk Engine High-Throughput and Latency Benchmarks."""

import asyncio
from decimal import Decimal
import time
import pytest
from openquant.adapters.risk.risk_engine import SynchronousRiskEngine
from openquant.domain.models.order import OrderRequest, OrderSide, OrderType
from openquant.domain.models.risk import RiskLimitsConfig


@pytest.fixture
def risk_engine() -> SynchronousRiskEngine:
    cfg = RiskLimitsConfig(
        max_daily_loss_percent=5.0,
        max_drawdown_percent=10.0,
        max_orders_per_second=100,
    )
    return SynchronousRiskEngine(config=cfg)


@pytest.mark.asyncio
async def test_risk_engine_sequential_throughput(risk_engine: SynchronousRiskEngine):
    """Benchmark: 50 sequential evaluations against all pre-trade hard stops."""
    iterations = 50
    req = OrderRequest(
        account_id="ACC_BENCHMARK",
        broker_id="paper",
        strategy_id="strat_bench",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("10"),
        price=Decimal("150.00"),
        idempotency_key="idem_bench",
    )

    start = time.perf_counter()
    for _ in range(iterations):
        res = await risk_engine.evaluate_order(
            request=req,
            current_market_price=Decimal("150.00"),
            daily_loss_percent=1.2,
            current_drawdown_percent=2.5,
        )
        assert res.allowed is True
    total_time = time.perf_counter() - start

    avg_ms = (total_time / iterations) * 1000.0
    throughput = iterations / total_time

    # Performance assertion: Sub-2ms evaluation per check
    assert avg_ms < 2.0, f"Average latency {avg_ms:.3f}ms exceeded 2ms threshold"
    assert throughput > 500, f"Throughput {throughput:.1f} ops/sec below 500 ops/sec target"


@pytest.mark.asyncio
async def test_risk_engine_parallel_concurrency_throughput(risk_engine: SynchronousRiskEngine):
    """Benchmark: 50 parallel concurrent evaluations."""
    iterations = 50
    req = OrderRequest(
        account_id="ACC_BENCHMARK",
        broker_id="paper",
        strategy_id="strat_bench",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("5"),
        price=Decimal("150.00"),
        idempotency_key="idem_parallel_bench",
    )

    async def single_eval(idx: int):
        return await risk_engine.evaluate_order(
            request=req,
            current_market_price=Decimal("150.00"),
            daily_loss_percent=0.5,
            current_drawdown_percent=1.0,
        )

    start = time.perf_counter()
    tasks = [single_eval(i) for i in range(iterations)]
    results = await asyncio.gather(*tasks)
    total_time = time.perf_counter() - start

    assert len(results) == iterations
    assert all(r.allowed for r in results)

    throughput = iterations / total_time
    assert throughput > 500, f"Parallel throughput {throughput:.1f} ops/sec below 500 ops/sec"
