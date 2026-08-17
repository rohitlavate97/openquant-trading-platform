"""Unit tests for Strategy Application Service."""

import pytest
from openquant.application.services.strategy_service import StrategyService
from openquant.adapters.strategy.strategy_engine import StrategyEngine
from openquant.adapters.sandbox.runner import StrategySandboxRunner
from openquant.application.services.audit_service import AuditLogService
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.domain.models.strategy import StrategyState, StrategyParameter


@pytest.fixture
def strategy_service_instance():
    engine = StrategyEngine(sandbox=StrategySandboxRunner())
    audit = AuditLogService(audit_repo=InMemoryAuditLogRepository())
    return StrategyService(engine=engine, sandbox=StrategySandboxRunner(), audit=audit)


@pytest.mark.asyncio
async def test_strategy_service_create_and_lifecycle(strategy_service_instance):
    """Verify strategy creation, AST validation, start, pause, stop lifecycle."""
    source_code = """
# EMAMomentumStrategy
fast_sma = 0
"""
    strat = await strategy_service_instance.create_strategy(
        name="Test Momentum",
        source_code=source_code,
        description="Testing service lifecycle",
        symbols=["AAPL"],
        parameters=[StrategyParameter(name="fast_period", default_value=3, current_value=3)],
    )

    assert strat.strategy_id.startswith("strat_")
    assert strat.name == "Test Momentum"
    assert strat.state == StrategyState.INITIALIZED

    # Start
    start_ok = await strategy_service_instance.start_strategy(strat.strategy_id)
    assert start_ok is True
    fetched = await strategy_service_instance.get_strategy(strat.strategy_id)
    assert fetched.state == StrategyState.RUNNING

    # Pause
    pause_ok = await strategy_service_instance.pause_strategy(strat.strategy_id)
    assert pause_ok is True
    assert (await strategy_service_instance.get_strategy(strat.strategy_id)).state == StrategyState.PAUSED

    # Stop
    stop_ok = await strategy_service_instance.stop_strategy(strat.strategy_id)
    assert stop_ok is True
    assert (await strategy_service_instance.get_strategy(strat.strategy_id)).state == StrategyState.STOPPED


@pytest.mark.asyncio
async def test_strategy_service_rejects_unsafe_ast_code(strategy_service_instance):
    """Verify strategy creation raises ValueError if code contains dangerous imports."""
    bad_code = "import os\nos.system('echo exploit')"
    with pytest.raises(ValueError, match="AST security validation"):
        await strategy_service_instance.create_strategy(
            name="Exploit Strategy",
            source_code=bad_code,
        )
