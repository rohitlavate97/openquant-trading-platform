# OpenQuant Backend Core

Enterprise-grade algorithmic trading platform backend written in Python 3.13 and FastAPI.

## Architecture

Built on **Clean Architecture / Hexagonal Architecture** principles:
- **Domain Layer (`src/openquant/domain/`)**: Pure business logic, value objects, domain entities, and abstract port interfaces (`IBrokerAdapter`, `IStrategySandbox`, `IOrderRepository`, etc.). Strictly independent of infrastructure, broker SDKs, and web frameworks.
- **Adapters Layer (`src/openquant/adapters/`)**: Concrete implementations of secondary ports (Broker Adapters, Strategy Sandboxes, Database Persistence, Event Bus).
- **Application Layer (`src/openquant/application/`)**: Use cases orchestrating domain flows (Order Management System, Risk Engine, Strategy Promotion Gate).
- **Interfaces Layer (`src/openquant/interfaces/`)**: Primary driving adapters (FastAPI REST endpoints, WebSocket streams, CLI).

## Local Development

```bash
# Sync dependencies with Python 3.13
uv sync --all-extras --dev

# Run tests with structural boundary validation
uv run pytest

# Start development server
uv run uvicorn openquant.interfaces.api.app:create_app --factory --reload --port 8000
```
