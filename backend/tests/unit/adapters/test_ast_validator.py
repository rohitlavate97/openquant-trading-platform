"""Unit tests for AST Security Validator and Strategy Execution Sandbox."""

from openquant.adapters.sandbox.ast_validator import ASTSecurityValidator


def test_ast_validator_rejects_eval_and_exec():
    """Verify eval() and exec() are flagged and rejected."""
    code_eval = "x = 10\nresult = eval('x + 5')"
    res = ASTSecurityValidator.validate(code_eval)
    assert res.is_safe is False
    assert any("eval" in v for v in res.violations)

    code_exec = "exec('import os')"
    res = ASTSecurityValidator.validate(code_exec)
    assert res.is_safe is False
    assert any("exec" in v for v in res.violations)


def test_ast_validator_rejects_file_io_open():
    """Verify open() is flagged and rejected."""
    code_open = "with open('/etc/passwd', 'r') as f:\n    data = f.read()"
    res = ASTSecurityValidator.validate(code_open)
    assert res.is_safe is False
    assert any("open" in v for v in res.violations)


def test_ast_validator_rejects_prohibited_modules():
    """Verify os, subprocess, socket, requests imports are rejected."""
    for mod in ["os", "sys", "subprocess", "socket", "requests", "urllib.request"]:
        code = f"import {mod}\nprint('attempt')"
        res = ASTSecurityValidator.validate(code)
        assert res.is_safe is False
        assert any(mod in v for v in res.violations)


def test_ast_validator_rejects_introspection_escapes():
    """Verify __subclasses__ and __globals__ introspection escapes are blocked."""
    code_subclasses = "classes = ().__class__.__bases__[0].__subclasses__()"
    res = ASTSecurityValidator.validate(code_subclasses)
    assert res.is_safe is False
    assert any("__subclasses__" in v or "__bases__" in v for v in res.violations)


def test_ast_validator_allows_clean_quantitative_logic():
    """Verify pure math and algorithmic strategy logic passes validation."""
    clean_code = """
def calculate_moving_average(prices, window=20):
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window

prices = [100.0, 101.5, 102.0, 99.5, 103.0]
ma = calculate_moving_average(prices, window=3)
result = {"signal": "BUY" if ma and ma > 100 else "HOLD"}
"""
    res = ASTSecurityValidator.validate(clean_code)
    assert res.is_safe is True
    assert len(res.violations) == 0
