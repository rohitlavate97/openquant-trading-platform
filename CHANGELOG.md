# Changelog

All notable changes to the OpenQuant algorithmic trading platform are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - Milestone 07: Order Management System (OMS)

### Added
- **OMS Application Service (`src/openquant/application/services/order_service.py`)**:
  - Strict idempotency validation against `(account_id, idempotency_key)` preventing duplicate live broker executions on retries.
  - Complete order lifecycle state machine: `PENDING_SUBMISSION` -> `SUBMITTED` -> `OPEN` -> `PARTIALLY_FILLED` -> `FILLED` / `CANCELLED` / `REJECTED`.
  - Real-time weighted average entry price and realized/unrealized PnL portfolio accounting.
  - Automated continuous position reconciliation engine comparing internal OMS actuals against live broker positions.
- **OMS Repositories & Exceptions**:
  - `InMemoryOrderRepository`, `InMemoryPositionRepository`, `OrderCancellationError`.
- **OMS REST Endpoints (`src/openquant/interfaces/api/v1/endpoints/orders.py`)**:
  - `POST /api/v1/orders`, `GET /api/v1/orders`, `GET /api/v1/orders/{order_id}`, `DELETE /api/v1/orders/{order_id}`, `GET /api/v1/positions`, `POST /api/v1/positions/reconcile`.
- **Frontend Order Management UI (`frontend/src/features/orders/OrderManagementPage.tsx`)**:
  - Direct Order Ticket with Side/Type/Price selectors and UUID idempotency key generator.
  - Active & Historical Orders Table with fill progress bars and 1-click cancel buttons.
  - Live Portfolio Positions table with realized/unrealized PnL badges and 1-click "Reconcile Broker" trigger.

---

## [0.6.0] - Milestone 06: Market Data Ingestion & Staleness Engine

### Added
- **Market Data Domain Models & Ports (`src/openquant/domain/models/market_data.py`, `src/openquant/domain/ports/market_data_port.py`)**:
  - `FeedHealthStatus`, `SymbolFeedMetrics`, `MarketDataStalenessReport`, `IMarketDataPort`, `ICandleAggregatorPort`.
- **In-Memory Feed & Staleness Engine (`src/openquant/adapters/market_data/in_memory_feed.py`)**:
  - Real-time tick caching, latency tracking, tick frequency profiling, and pre-trade 3000ms staleness threshold enforcement.
- **Streaming Multi-Timeframe Candle Aggregator (`src/openquant/adapters/market_data/candle_aggregator.py`)**:
  - Multi-timeframe OHLCV bar builder (`1m`, `5m`, `15m`, `1h`, `4h`, `1d`) with boundary finalization.
- **Synthetic Market Data Generator (`src/openquant/adapters/market_data/synthetic_feed.py`)**:
  - Multi-asset geometric Brownian random walk simulator with realistic bid/ask spread modeling and configurable frequency.
- **Market Data REST Endpoints (`src/openquant/interfaces/api/v1/endpoints/market_data.py`)**:
  - `/api/v1/market-data/ticks/latest`, `/api/v1/market-data/candles`, `/api/v1/market-data/staleness`, `/api/v1/market-data/ticks`, `/api/v1/market-data/replay/start` & `stop`.
- **Frontend Market Data & Feed Health UI (`frontend/src/features/market-data/MarketDataManagementPage.tsx`)**:
  - System-wide feed health dashboard, per-symbol latency monitor table, synthetic replay generator controls, and OHLCV candle bar visualizer.

---

## [0.5.0] - Milestone 05: Unified REST & WebSocket Layer

### Added
- **Multiplexed WebSocket Connection Manager (`src/openquant/interfaces/api/v1/websocket/connection_manager.py`)**:
  - Thread-safe connection management and channel-based topic subscriptions for market data (`ticks:{symbol}`, `ticks:ALL`), orders (`orders:{account_id}`, `orders:ALL`), and telemetry (`telemetry:global`).
- **WebSocket Streaming Endpoints (`/ws/v1/`)**:
  - `/ws/v1/market-data`: Real-time L1 tick streaming with subscribe/unsubscribe action protocol and ping/pong heartbeats.
  - `/ws/v1/orders`: Live order execution reports and status updates.
  - `/ws/v1/telemetry`: Platform latency, risk halts, and kill switch status broadcasting.
- **Streaming Broadcaster Application Service (`src/openquant/application/services/streaming_service.py`)**:
  - Dispatches domain ticks and order execution reports to active WebSocket client pools.
  - `/api/v1/stream/stats` REST endpoint exposing active connection and subscription counts.
- **Frontend Real-Time Market Ticker (`frontend/src/features/market-data/LiveMarketTicker.tsx`)**:
  - Resilient `useWebSocket` hook with exponential backoff auto-reconnect.
  - Live streaming ticker cards with green/red price flash animations, bid/ask spread indicators, and dynamic symbol tracking.

---

## [0.4.0] - Milestone 04: Broker Adapter Interface & First Adapter

### Added
- **Multi-Broker Hexagonal Port (`src/openquant/domain/ports/broker_adapter.py`)**:
  - `IBrokerAdapter` defining standardized contract for connection, token handshake, order execution, position reconciliation, funds inspection, holdings retrieval, and real-time tick/execution streaming.
- **High-Fidelity Paper Broker Adapter (`src/openquant/adapters/brokers/paper_adapter.py`)**:
  - `PaperBrokerAdapter` supporting simulated order matching, configurable slippage, cash/margin tracking, and real-time PnL computation.
- **Production Zerodha Kite Connect Adapter (`src/openquant/adapters/brokers/zerodha_adapter.py`)**:
  - `ZerodhaKiteAdapter` for Zerodha Kite Connect v3 REST API supporting equity, futures, options, margin queries, positions, and holdings.
- **Automated Certification & Security Audit Harness (`src/openquant/adapters/brokers/certification_harness.py`)**:
  - Systematic 5-point verification suite (`CREDENTIAL_LEAKAGE_AUDIT`, `AUTH_HANDSHAKE_VALIDATION`, `SANDBOX_ORDER_LIFECYCLE`, `POSITIONS_AND_FUNDS_INTEGRITY`, `FAULT_TOLERANCE_AND_SHUTDOWN`) enforcing Non-Negotiable Rule 9 before Live Trading.
- **Broker Management REST Endpoints**:
  - `/api/v1/brokers`, `/api/v1/brokers/{adapter_id}/metadata`, `/api/v1/brokers/{adapter_id}/connect`, `/api/v1/brokers/{adapter_id}/funds`, `/api/v1/brokers/{adapter_id}/certify`.
- **Frontend Broker Management UI**:
  - `BrokerAdaptersPage.tsx` with registered adapter grid, live certification badges, real-time funds and margin metrics, and 1-click audit harness runner.

---

## [0.3.0] - Milestone 03: Database Foundation & Audit Logging

### Added
- **Async SQLAlchemy 2.x Schema & Models (`src/openquant/adapters/database/models.py`)**:
  - `UserModel`, `APIKeyModel`, `BrokerCredentialModel` with user-scoped foreign keys and cascade rules.
  - `OrderModel` with unique composite index on `(account_id, idempotency_key)` preventing order duplication.
  - `PositionModel` with unique composite index on `(account_id, symbol)` for real-time reconciled position tracking.
  - `StrategyModel` and `PromotionRecordModel` tracking strategy metadata and immutable promotion gate transitions.
  - `AuditLogModel` append-only table indexed by `(event_type, timestamp)` and `(actor_id, timestamp)`.
- **Alembic Database Migration Pipeline**:
  - `alembic.ini`, async migration environment `env.py`, and initial migration `0001_initial_schema.py`.
- **SQLAlchemy 2.x Async Repositories**:
  - `SQLAlchemyUserRepository`, `SQLAlchemyAPIKeyRepository`, `SQLAlchemyCredentialVaultRepository`, `SQLAlchemyOrderRepository`, `SQLAlchemyPositionRepository`, `SQLAlchemyStrategyRepository`, `SQLAlchemyAuditLogRepository`.
- **Audit Logging Application Service & API**:
  - `AuditLogService` for structured event recording across system, risk, auth, and promotion boundaries.
  - `/api/v1/audit-logs` endpoint with pagination and severity/actor/event_type filtering.
- **Frontend Audit Trail Viewer**:
  - `AuditLogViewer.tsx` component with severity badges, search bar, and structured JSON payload inspector modal.
  - New "Audit Trail" navigation tab in platform layout.

---

## [0.2.0] - Milestone 02: Authentication, RBAC & Secrets Management

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
