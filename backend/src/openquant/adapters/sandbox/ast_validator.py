"""AST Static Analysis Validator for Strategy Execution Security.

Enforces strict allowlisting and detects forbidden builtins, unauthorized imports,
and dangerous reflection/introspection patterns before strategy code is ever executed.
"""

import ast
from openquant.domain.ports.strategy_sandbox import SandboxSecurityCheckResult

# Blocked built-in function names
FORBIDDEN_BUILTINS = {
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "input",
    "breakpoint",
    "memoryview",
    "help",
    "exit",
    "quit",
}

# Strictly forbidden modules that attempt I/O, subprocess execution, or arbitrary networking
FORBIDDEN_MODULES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "shutil",
    "pty",
    "commands",
    "ctypes",
    "tempfile",
    "urllib",
    "requests",
    "httpx",
    "aiohttp",
    "webbrowser",
    "posix",
    "nt",
    "_thread",
    "signal",
    "asyncio.subprocess",
    "pickle",
    "shelve",
    "marshal",
}

# Forbidden attribute lookups that enable sandbox escapes via Python introspection
FORBIDDEN_ATTRIBUTES = {
    "__globals__",
    "__subclasses__",
    "__code__",
    "__closure__",
    "__builtins__",
    "__bases__",
    "__mro__",
    "gi_frame",
    "cr_frame",
    "f_locals",
    "f_globals",
    "f_builtins",
}


class StrategyASTVisitor(ast.NodeVisitor):
    """AST visitor traversing the abstract syntax tree to flag security violations."""

    def __init__(self) -> None:
        self.violations: list[str] = []
        self.detected_imports: list[str] = []
        self.dangerous_nodes: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            module_name = alias.name.split(".")[0]
            self.detected_imports.append(alias.name)
            if alias.name in FORBIDDEN_MODULES or module_name in FORBIDDEN_MODULES:
                self.violations.append(
                    f"Line {node.lineno}: Prohibited module import '{alias.name}' is forbidden in Strategy Sandbox."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            module_base = node.module.split(".")[0]
            self.detected_imports.append(node.module)
            if node.module in FORBIDDEN_MODULES or module_base in FORBIDDEN_MODULES:
                self.violations.append(
                    f"Line {node.lineno}: Prohibited module import 'from {node.module}' is forbidden in Strategy Sandbox."
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check direct calls e.g. eval(), exec(), open()
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BUILTINS:
            self.violations.append(
                f"Line {node.lineno}: Direct call to forbidden builtin '{node.func.id}()' is prohibited."
            )
            self.dangerous_nodes.append(node.func.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Check introspection/sandbox escape attribute lookups
        if node.attr in FORBIDDEN_ATTRIBUTES:
            self.violations.append(
                f"Line {node.lineno}: Access to dangerous internal attribute '{node.attr}' is prohibited."
            )
            self.dangerous_nodes.append(node.attr)
        self.generic_visit(node)


class ASTSecurityValidator:
    """Static analyzer evaluating strategy code safety."""

    @staticmethod
    def validate(source_code: str) -> SandboxSecurityCheckResult:
        """Parse and analyze Python source code. Returns validation result."""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return SandboxSecurityCheckResult(
                is_safe=False,
                violations=[f"Syntax error in strategy code: {e}"],
                detected_imports=[],
                dangerous_nodes=["SyntaxError"],
            )

        visitor = StrategyASTVisitor()
        visitor.visit(tree)

        is_safe = len(visitor.violations) == 0
        return SandboxSecurityCheckResult(
            is_safe=is_safe,
            violations=visitor.violations,
            detected_imports=visitor.detected_imports,
            dangerous_nodes=visitor.dangerous_nodes,
        )
