"""Hexagonal Port: Abstract Strategy Execution Sandbox.

Enforces strict isolation, resource quotas, and capability allowlisting
for user-provided and AI-generated strategy execution.
"""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field


class SandboxSecurityCheckResult(BaseModel):
    """Result of static AST analysis and capability linting on strategy code."""
    is_safe: bool
    violations: list[str] = Field(default_factory=list)
    detected_imports: list[str] = Field(default_factory=list)
    dangerous_nodes: list[str] = Field(default_factory=list)


class SandboxExecutionResult(BaseModel):
    """Result of executing strategy code inside isolated sandbox environment."""
    success: bool
    execution_time_seconds: float
    memory_used_mb: float
    cpu_time_seconds: float
    output: Any = None
    error_message: str | None = None
    resource_limit_exceeded: bool = False


class IStrategySandbox(ABC):
    """Abstract port for strategy code analysis, compilation, and isolated execution."""

    @abstractmethod
    def validate_code_ast(self, source_code: str) -> SandboxSecurityCheckResult:
        """Perform static AST security analysis checking for forbidden operations and imports."""

    @abstractmethod
    async def execute_isolated(
        self,
        strategy_id: str,
        source_code: str,
        context: dict[str, Any],
        max_cpu_seconds: int = 30,
        max_memory_mb: int = 512,
        timeout_seconds: int = 60,
    ) -> SandboxExecutionResult:
        """Execute strategy code inside an isolated, resource-constrained environment."""

    @abstractmethod
    async def terminate_execution(self, strategy_id: str) -> bool:
        """Forcefully terminate a running strategy execution instance."""
