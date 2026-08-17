# Changelog

All notable changes to the OpenQuant algorithmic trading platform are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - Milestone 11: Backtesting Engine & Walk-Forward Validation

### Added
- **Event-Driven Backtesting Engine (`src/openquant/adapters/backtest/event_driven_engine.py`)**:
  - Implements `IBacktestEngine` port for chronological market bar execution.
  - Realistic Slippage Model (configurable basis points) and Commission deduction.
  - Performance statistics: CAGR %, Sharpe Ratio, Sortino Ratio, Max Drawdown %, Profit Factor, Win Rate %, Average Win/Loss.
  - Chronological trade log and marked-to-market equity curve generation.
- **Walk-Forward Validation Engine**:
  - Multi-window rolling In-Sample vs Out-of-Sample efficiency validation.
  - Walk-Forward Efficiency (WFE) Ratio computation and Overfitting Risk score (`LOW`, `MEDIUM`, `HIGH`).
- **Backtest Application Service (`src/openquant/application/services/backtest_service.py`)**:
  - Synthetic historical candle generator with realistic random walk volatility.
  - Non-negotiable Stage 2 Promotion Gate criteria evaluation (`DRAFT` → `BACKTEST`).
- **Backtest REST API (`src/openquant/interfaces/api/v1/endpoints/backtest.py`)**:
  - `POST /api/v1/backtest/run`, `POST /api/v1/backtest/walk-forward`, `GET /api/v1/backtest/results/{backtest_id}`, `POST /api/v1/backtest/{backtest_id}/promote`.
- **Frontend Backtest Dashboard UI (`frontend/src/features/backtesting/BacktestDashboardPage.tsx`)**:
  - Backtest configuration bar, interactive SVG marked-to-market equity curve, trade log table, multi-window WFE comparison table, and 1-click Stage 2 Promotion action.

---

## [0.10.0] - Milestone 10: Strategy Engine (Python Source)

### Added
- **Strategy Execution Engine Runtime (`src/openquant/adapters/strategy/strategy_engine.py`)**:
  - Implements `IStrategyEngine` coordinating Python strategy instance registration, compilation, and isolated event dispatching.
  - Event hooks: `on_start(context)`, `on_tick(tick, context)`, `on_bar(candle, context)`, `on_order_event(report, context)`, `on_stop(context)`.
- **Strategy Base Framework & Standard Algorithms (`src/openquant/strategies/`)**:
  - `BaseStrategy` and `StrategyContext` with `buy()`, `sell()`, and `emit_signal()` generating valid `idempotency_key` values.
  - Standard builtin strategies: `EMAMomentumStrategy` (moving average crossover) and `RSIMeanReversionStrategy` (oversold/overbought mean reversion).
- **Strategy Application Service (`src/openquant/application/services/strategy_service.py`)**:
  - Full CRUD lifecycle with mandatory pre-execution AST static analysis security validation.
  - Structured immutable compliance logging via `IAuditLogRepository`.
- **Strategy REST Endpoints (`src/openquant/interfaces/api/v1/endpoints/strategies.py`)**:
  - `POST /api/v1/strategies`, `GET /api/v1/strategies`, `GET /api/v1/strategies/{strategy_id}`, `PUT /api/v1/strategies/{strategy_id}`, `POST /api/v1/strategies/{strategy_id}/start`, `POST /api/v1/strategies/{strategy_id}/stop`, `POST /api/v1/strategies/{strategy_id}/pause`, `GET /api/v1/strategies/{strategy_id}/logs`.
- **Frontend Strategy Engine UI (`frontend/src/features/strategies/StrategyManagementPage.tsx`)**:
  - Strategy Catalog, state badges (`INITIALIZED`, `RUNNING`, `PAUSED`, `STOPPED`, `ERROR`), 1-click execution controls, PnL & Win Rate metrics, Python source viewer, real-time diagnostic event stream, and Deploy Strategy modal.

---

## [0.9.0] - Milestone 09: Strategy Execution Sandbox

### Added
- **Process-Isolated Strategy Sandbox (`src/openquant/adapters/sandbox/runner.py`)**:
  - Isolated Python execution with CPU, RAM (512MB), and wall-clock timeout quotas.
  - Safe import allowlisting hook supporting standard quant modules (`math`, `decimal`, `datetime`, `time`, `json`) while prohibiting unauthorized imports.
  - Print log redirection for real-time strategy debugging and telemetry capture.
- **AST Static Analysis & Security Validator (`src/openquant/adapters/sandbox/ast_validator.py`)**:
  - Traverses syntax tree prior to execution and flags prohibited builtins (`eval`, `exec`, `open`, `__import__`, `exit`, etc.).
  - Blocks dangerous system modules (`os`, `sys`, `subprocess`, `socket`, `ctypes`, `urllib`, `requests`, etc.) and reflection exploits (`__globals__`, `__subclasses__`).
- **Strategy Sandbox Application Service (`src/openquant/application/services/sandbox_service.py`)**:
  - Pre-built quant templates: Exponential Moving Average Momentum, RSI Mean Reversion, and Donchian Breakout.
  - Compliance audit logging of sandbox validation failures and executions in `IAuditLogRepository`.
- **Sandbox REST Endpoints (`src/openquant/interfaces/api/v1/endpoints/sandbox.py`)**:
  - `POST /api/v1/sandbox/validate`, `POST /api/v1/sandbox/execute`, `GET /api/v1/sandbox/templates`.
- **Frontend Strategy Sandbox UI (`frontend/src/features/sandbox/StrategySandboxPage.tsx`)**:
  - Code Editor with template switcher, live AST security scanner, and execution output terminal with resource metrics.

---

## [0.8.0] - Milestone 08: Risk Engine & Global Kill Switch

### Added
- **Synchronous Pre-Trade Risk Engine (`src/openquant/adapters/risk/risk_engine.py`)**:
  - Pre-trade blocking on every order with zero async bypass (Non-Negotiable Rule 2 & 4).
  - 8 synchronous checks: Kill switch status, daily loss % (3.0%), peak drawdown % (5.0%), sliding-window rate limit (10 orders/sec), position size cap (10.0% of equity), self-trade crossing prevention, and max open orders per symbol (10).
- **Risk Application Service (`src/openquant/application/services/risk_service.py`)**:
  - 1-Click Emergency Kill Switch orchestration across GLOBAL, ACCOUNT, STRATEGY, and SYMBOL scopes.
  - Automatic mass cancellation of active open orders upon emergency trigger.
  - Real-time WebSocket broadcasting of risk rejections and kill switch status changes.
- **Risk REST Endpoints (`src/openquant/interfaces/api/v1/endpoints/risk.py`)**:
  - `GET /api/v1/risk/config`, `PUT /api/v1/risk/config`, `POST /api/v1/risk/kill-switch/activate`, `POST /api/v1/risk/kill-switch/deactivate`, `POST /api/v1/risk/evaluate-pre-trade`.
- **Frontend Risk Management UI (`frontend/src/features/risk/RiskManagementPage.tsx`)**:
  - Emergency Kill Switch banner and modal with level selectors and position flattening toggle.
  - Interactive Pre-Trade Hard-Stop Parameters form with range sliders.
  - Pre-Trade Risk Engine Dry-Run Simulator visualizer with individual rule pass/fail badges.

---

## [0.7.0] - Milestone 07: Order Management System (OMS)

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
