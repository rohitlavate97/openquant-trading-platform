"""Unit tests for Strategy Execution Sandbox Application Service and AST Validator."""

import pytest
from openquant.adapters.sandbox.runner import StrategySandboxRunner
from openquant.application.services.sandbox_service import StrategySandboxService
from openquant.application.services.audit_service import AuditLogService
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository


@pytest.fixture
def sandbox_service_instance():
    runner = StrategySandboxRunner()
    audit = AuditLogService(audit_repo=InMemoryAuditLogRepository())
    return StrategySandboxService(runner=runner, audit=audit)


def test_sandbox_ast_validation_allows_clean_quant_code(sandbox_service_instance):
    """Verify safe mathematical / quant code passes AST static analysis."""
    clean_code = """
import math
prices = context.get('prices', [100.0, 102.0, 105.0])
mean = sum(prices) / len(prices)
variance = sum((p - mean) ** 2 for p in prices) / len(prices)
std_dev = math.sqrt(variance)
result = {"mean": mean, "std_dev": std_dev}
"""
    check = sandbox_service_instance.validate_code(clean_code)
    assert check.is_safe is True
    assert len(check.violations) == 0


def test_sandbox_ast_validation_blocks_dangerous_operations(sandbox_service_instance):
    """Verify AST security validator flags forbidden modules and builtin calls."""
    dangerous_code = """
import os
import subprocess
import socket

def exploit():
    os.system("rm -rf /")
    eval("1 + 1")
    f = open("/etc/passwd", "r")
"""
    check = sandbox_service_instance.validate_code(dangerous_code)
    assert check.is_safe is False
    assert len(check.violations) >= 3
    assert any("os" in v for v in check.violations)
    assert any("subprocess" in v for v in check.violations)
    assert any("eval" in v for v in check.violations)


@pytest.mark.asyncio
async def test_sandbox_execute_strategy_with_print_capture(sandbox_service_instance):
    """Verify isolated execution returns correct result dict and captures stdout logs."""
    strategy_code = """
prices = context.get('prices', [10.0, 20.0, 30.0])
print("Processing tick batch...")
avg_price = sum(prices) / len(prices)
print(f"Computed average: {avg_price}")
result = {"avg_price": avg_price, "action": "BUY"}
"""
    res = await sandbox_service_instance.execute_strategy(
        source_code=strategy_code,
        context={"prices": [10.0, 20.0, 30.0]},
        strategy_id="strat_test_1",
    )
    assert res.success is True
    assert res.output["avg_price"] == 20.0
    assert "Processing tick batch..." in res.output["_logs"]
    assert "Computed average: 20.0" in res.output["_logs"]
    assert res.execution_time_seconds >= 0.0


@pytest.mark.asyncio
async def test_sandbox_execute_blocks_unsafe_code_pre_execution(sandbox_service_instance):
    """Verify dangerous code is rejected prior to execution with zero runtime exposure."""
    bad_code = "import sys; sys.exit(0)"
    res = await sandbox_service_instance.execute_strategy(
        source_code=bad_code,
        strategy_id="strat_bad",
    )
    assert res.success is False
    assert "AST Security Violation" in res.error_message


@pytest.mark.asyncio
async def test_sandbox_execute_timeout_enforcement(sandbox_service_instance):
    """Verify long-running execution is terminated by sandbox timeout budget."""
    infinite_loop = """
import time
time.sleep(2)
"""
    res = await sandbox_service_instance.execute_strategy(
        source_code=infinite_loop,
        strategy_id="strat_loop",
        timeout_seconds=1,
    )
    assert res.success is False
    assert res.resource_limit_exceeded is True
    assert "timed out" in res.error_message
