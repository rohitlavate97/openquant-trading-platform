"""Adversarial Sandbox Escape, AST Static Analysis, and Resource Starvation Penetration Tests."""

import pytest
from openquant.adapters.sandbox.ast_validator import ASTSecurityValidator
from openquant.adapters.sandbox.runner import StrategySandboxRunner


@pytest.fixture
def runner() -> StrategySandboxRunner:
    return StrategySandboxRunner()


def test_adversarial_direct_os_import_blocked():
    payload = """
import os
def on_tick(tick):
    os.system('rm -rf /')
"""
    result = ASTSecurityValidator.validate(payload)
    assert not result.is_safe
    assert any("os" in err for err in result.violations)


def test_adversarial_subprocess_import_blocked():
    payload = """
import subprocess
def on_tick(tick):
    subprocess.Popen(['curl', 'http://malicious.com'])
"""
    result = ASTSecurityValidator.validate(payload)
    assert not result.is_safe
    assert any("subprocess" in err for err in result.violations)


def test_adversarial_dynamic_import_call_blocked():
    payload = """
def on_tick(tick):
    m = __import__('os')
    m.system('ls')
"""
    result = ASTSecurityValidator.validate(payload)
    assert not result.is_safe
    assert any("__import__" in err for err in result.violations)


def test_adversarial_eval_exec_compile_blocked():
    eval_payload = "def on_tick(tick):\n    eval('2+2')"
    exec_payload = "def on_tick(tick):\n    exec('import sys')"
    compile_payload = "def on_tick(tick):\n    compile('pass', '', 'exec')"

    for code in [eval_payload, exec_payload, compile_payload]:
        res = ASTSecurityValidator.validate(code)
        assert not res.is_safe
        assert any(func in str(res.violations) for func in ["eval", "exec", "compile"])


def test_adversarial_builtins_and_dunder_inspection_blocked():
    payload = """
def on_tick(tick):
    subs = object.__subclasses__()
"""
    result = ASTSecurityValidator.validate(payload)
    assert not result.is_safe
    assert any("__subclasses__" in err for err in result.violations)


def test_adversarial_file_io_blocked():
    payload = """
def on_tick(tick):
    with open('/etc/passwd', 'r') as f:
        data = f.read()
"""
    result = ASTSecurityValidator.validate(payload)
    assert not result.is_safe
    assert any("open" in err for err in result.violations)


def test_adversarial_network_socket_blocked():
    payload = """
import socket
def on_tick(tick):
    s = socket.socket()
"""
    result = ASTSecurityValidator.validate(payload)
    assert not result.is_safe
    assert any("socket" in err for err in result.violations)


@pytest.mark.asyncio
async def test_runner_rejects_unsafe_code_pre_execution(runner: StrategySandboxRunner):
    unsafe_code = """
import sys
def on_tick(tick):
    sys.exit(1)
"""
    res = await runner.execute_isolated(
        strategy_id="strat_unsafe",
        source_code=unsafe_code,
        context={},
    )
    assert not res.success
    assert "AST Security Validator" in (res.error_message or "")


@pytest.mark.asyncio
async def test_runner_enforces_execution_timeout(runner: StrategySandboxRunner):
    slow_code = """
import time
time.sleep(0.3)
"""
    result = await runner.execute_isolated(
        strategy_id="strat_slow",
        source_code=slow_code,
        context={},
        timeout_seconds=0.05,
    )
    assert not result.success
