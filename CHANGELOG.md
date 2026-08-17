# Changelog

All notable changes to the OpenQuant algorithmic trading platform are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - Milestone 02: Authentication, RBAC & Secrets Management

### Added
- **Authenticated Secrets Vault (`src/openquant/adapters/secrets/vault.py`)**:
  - `FernetSecretsVault` implementing `ISecretsManager` using authenticated encryption (AES-128-CBC + HMAC-SHA256) with PBKDF2-HMAC-SHA256 key derivation.
  - Zero plaintext leakage guarantee: secrets are decrypted strictly in-memory by authorized broker adapters and always masked (`••••••••1234`) in logs and API responses.
- **Multi-Tenant User Auth & Password Security**:
  - Direct `bcrypt` password hashing with auto-generated random salt.
  - JWT token generation & verification (`access` 60m, `refresh` 7d).
- **Role-Based Access Control (RBAC)**:
  - 5 Hierarchical roles (`SUPER_ADMIN`, `ADMIN`, `QUANT_DEVELOPER`, `TRADER`, `VIEWER`).
  - 8 Granular permissions (`SYSTEM_ADMIN`, `KILL_SWITCH_TRIGGER`, `STRATEGY_CREATE`, `STRATEGY_APPROVE`, `LIVE_TRADING_ENABLE`, `BROKER_MANAGE`, `ORDER_MANAGE`, `READ_ONLY`).
  - FastAPI dependency factories `require_permissions` and `require_role`.
- **Programmatic API Keys**:
  - Cryptographic API key generation (`oq_live_...`), SHA-256 storage, and `X-API-Key` request header authentication.
- **REST Endpoints**:
  - `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/auth/me`.
  - `/api/v1/api-keys` (create, list, revoke).
  - `/api/v1/secrets/broker-credentials` (store, list masked, revoke).
- **Frontend Security UI**:
  - Zustand auth store with permission checks.
  - `BrokerCredentialsVault` interface with masked key views and encrypted credential management.
  - `APIKeyManagement` interface with 1-click copy for newly generated keys.

---

## [0.1.0] - Milestone 01: Project Setup & Hexagonal Boundaries

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
