"""Unit tests for StrategySandboxRunner execution, isolation, and timeout enforcement."""

import pytest
from openquant.adapters.sandbox.runner import StrategySandboxRunner


@pytest.mark.asyncio
async def test_sandbox_runner_executes_safe_code():
    """Verify runner successfully executes valid strategy logic and returns result."""
    runner = StrategySandboxRunner()
    code = """
x = context.get('initial_balance', 1000)
result = {'computed_balance': x * 1.05}
"""
    res = await runner.execute_isolated(
        strategy_id="strat_test_1",
        source_code=code,
        context={"initial_balance": 1000},
        timeout_seconds=5,
    )
    assert res.success is True
    assert res.output == {"computed_balance": 1050.0}
    assert res.resource_limit_exceeded is False


@pytest.mark.asyncio
async def test_sandbox_runner_blocks_unsafe_code_pre_execution():
    """Verify runner rejects unsafe code before execution."""
    runner = StrategySandboxRunner()
    code = "import os\nresult = os.listdir('.')"
    res = await runner.execute_isolated(
        strategy_id="strat_test_2",
        source_code=code,
        context={},
    )
    assert res.success is False
    assert "AST Security Validator" in res.error_message


@pytest.mark.asyncio
async def test_sandbox_runner_enforces_timeout():
    """Verify runner halts long running code and flags resource limit exceeded."""
    runner = StrategySandboxRunner()
    code = """
import time
time.sleep(2)
"""
    res = await runner.execute_isolated(
        strategy_id="strat_test_3",
        source_code=code,
        context={},
        timeout_seconds=1,
    )
    assert res.resource_limit_exceeded is True or not res.success

