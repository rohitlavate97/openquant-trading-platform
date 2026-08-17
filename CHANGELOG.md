# Changelog

All notable changes to the OpenQuant algorithmic trading platform are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - Milestone 01: Project Setup & Hexagonal Boundaries

### Added
- **Hexagonal Architecture Foundation**:
  - `src/openquant/domain`: Core domain models (`Order`, `Position`, `StrategyEntity`, `RiskCheckResult`, `Tick`), value objects, domain exceptions (`CapitalSafetyViolationError`, `KillSwitchActiveError`, `BrokerAdapterUncertifiedError`), and abstract ports (`IBrokerAdapter`, `IStrategySandbox`, `IOrderRepository`, `IEventBus`).
  - Strict AST-based structural architecture boundary test (`tests/unit/test_architecture_boundaries.py`) verifying domain layer has zero infrastructure dependencies.
- **Strategy Execution Sandbox Security**:
  - `ASTSecurityValidator` analyzing abstract syntax trees to block `eval`, `exec`, `open`, forbidden system/networking modules (`os`, `sys`, `subprocess`, `socket`, `requests`, `urllib`), and introspection sandbox escape vectors (`__globals__`, `__subclasses__`).
  - `StrategySandboxRunner` with execution time budgeting and restricted namespace execution.
- **Broker Adapter Layer Skeleton**:
  - `BaseBrokerAdapter` with certification checking and `BrokerAdapterRegistry` for tracking certified adapters.
- **FastAPI REST API Core**:
  - API v1 routing with `/health`, `/system/info`, and `/system/promotion-stages`.
  - Custom exception handlers mapping domain-level safety errors to structured HTTP responses.
- **Modern React/TypeScript Frontend**:
  - Institutional dark theme dashboard with Tailwind CSS.
  - Global 1-click **Kill Switch** component with confirmation modal and position-flattening toggle.
  - Interactive **Strategy Promotion Gate** pipeline visualizer displaying the 7-stage promotion lifecycle.
- **Testing & Tooling**:
  - Pytest test suite with 94% coverage across domain models, security AST validator, broker registry, and health API.
  - Vitest frontend component tests.
  - Docker Compose and GitHub Actions CI configuration.
