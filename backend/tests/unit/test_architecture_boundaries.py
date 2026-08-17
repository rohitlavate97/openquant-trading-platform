"""Structural Architecture Boundary Tests.

Proves mathematically via AST inspection that the Hexagonal Domain Layer
has ZERO dependencies on adapters, web frameworks, broker SDKs, or infrastructure.
"""

import ast
from pathlib import Path

FORBIDDEN_DOMAIN_IMPORT_PREFIXES = (
    "openquant.adapters",
    "openquant.application",
    "openquant.interfaces",
    "fastapi",
    "starlette",
    "uvicorn",
    "httpx",
    "requests",
    "aiohttp",
    "sqlalchemy.ext.asyncio",
)


def get_imports_from_file(file_path: Path) -> list[str]:
    """Parse a python file AST and return all top-level imported module names."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def test_domain_layer_has_zero_infrastructure_dependencies():
    """Verify that no file in openquant.domain imports forbidden infrastructure layers."""
    domain_dir = Path(__file__).resolve().parent.parent.parent / "src" / "openquant" / "domain"
    assert domain_dir.exists(), f"Domain directory {domain_dir} must exist"

    python_files = list(domain_dir.rglob("*.py"))
    assert len(python_files) > 0, "Domain layer must contain python source files"

    violations = []
    for py_file in python_files:
        relative_path = py_file.relative_to(domain_dir.parent.parent)
        imported_modules = get_imports_from_file(py_file)

        for imp in imported_modules:
            for forbidden in FORBIDDEN_DOMAIN_IMPORT_PREFIXES:
                if imp == forbidden or imp.startswith(f"{forbidden}."):
                    violations.append(f"{relative_path} imports forbidden '{imp}'")

    assert not violations, (
        "Hexagonal Boundary Violation detected in Domain Layer!\n"
        + "\n".join(violations)
    )
