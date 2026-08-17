# Changelog

All notable changes to the OpenQuant algorithmic trading platform are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - Milestone 22: Production Deployment

### Added
- **Multi-Stage Production Dockerfiles (`backend/Dockerfile.prod`, `frontend/Dockerfile.prod`, `frontend/nginx.prod.conf`)**:
  - Backend runtime container with non-root system user (`openquant:openquant`), `uv` dependency caching, and Uvicorn multi-worker parallel processes.
  - Frontend runtime container with Node 22 build to Alpine Nginx 1.27, SPA fallback, CSP/HSTS/X-Frame-Options security headers, and `/ws/` WebSockets proxying.
- **Production Docker Compose Stack (`docker-compose.prod.yml`)**:
  - PostgreSQL 16 Alpine with performance tuning, persistent data volume, and healthchecks.
  - Redis 7.2 with AOF persistence, password authentication, and memory limits.
  - Backend API engine, Frontend Nginx SPA, Prometheus v2.50 metrics collector, and Grafana 10.4 dashboard suite.
- **Kubernetes Helm 3.x Production Chart (`deployments/helm/openquant/`)**:
  - Full Helm chart templates: backend deployment, frontend deployment, ClusterIP services, ingress with TLS/cert-manager, HorizontalPodAutoscaler, ConfigMap, and Secrets.
- **Linux Systemd Service Units (`deployments/systemd/`)**:
  - `openquant-backend.service` and `openquant-worker.service` with kernel and filesystem sandboxing flags (`ProtectSystem=full`, `NoNewPrivileges=true`, `PrivateTmp=true`).
- **Production Configuration & Self-Hosting Documentation (`.env.production.example`, `docs/`)**:
  - Complete `.env.production.example` template with key generation guidelines.
  - `docs/self-hosting-guide.md` (bare-metal, Docker Compose, and Kubernetes deployment).
  - `docs/production-checklist.md` (10-point preflight verification checklist).
  - `docs/disaster-recovery.md` (PostgreSQL backup cron, restore drill, and Fernet master secret recovery).

## Milestone 21: Security Hardening & Load Testing

### Added
- **Automated Security Penetration Diagnostics Suite (`src/openquant/application/services/security_audit_service.py`, `src/openquant/interfaces/api/v1/endpoints/security.py`)**:
  - 6-point automated security verification matrix covering AST sandbox escape defense, AES-Fernet PBKDF2 secrets integrity, HMAC-SHA256 & nonce replay prevention, synchronous sub-millisecond risk evaluation latency, Rule 8 composite idempotency lock, and global kill switch interlock.
  - Endpoints: `GET /api/v1/security/audit-report` and `POST /api/v1/security/run-penetration-test`.
- **AST Sandbox Escape Penetration Tests (`backend/tests/security/test_sandbox_escape_penetration.py`)**:
  - Validates blocking of prohibited imports (`os`, `subprocess`, `socket`, `pty`), dynamic imports (`__import__`), reflection (`__subclasses__`), dangerous builtins (`eval`, `exec`, `compile`, `open`), and runaway execution timeout termination.
- **OMS Concurrency Stress & Race Condition Hardening (`backend/tests/stress/test_order_concurrency_stress.py`)**:
  - Verified 20 simultaneous submissions with identical `(account_id, idempotency_key)` preventing duplicate routing or position drift.
  - Tested 25 burst orders against synchronous pre-trade rate limiter and 30-order burst throughput with accurate atomic position accumulation.
- **Webhook Replay Attack & HMAC-SHA256 Security Tests (`backend/tests/security/test_webhook_replay_security.py`)**:
  - Validates constant-time signature verification, clock skew window ($\pm 60$s), and nonce deduplication cache.
- **Pre-Trade Risk Engine High-Throughput Benchmarks (`backend/tests/stress/test_risk_engine_throughput_benchmark.py`)**:
  - Validated 50 sequential and 50 concurrent pre-trade evaluations with sub-1ms latency ($> 500$ ops/sec).
- **Frontend Security Hardening Console (`frontend/src/features/security/SecurityHardeningPage.tsx`)**:
  - 100% Security Scorecard, verification matrix, 1-click penetration test runner, and capital safety rule guardrail cards.

## Milestone 20: Observability & Monitoring

### Added
- **Prometheus Metrics Collector (`src/openquant/adapters/observability/prometheus_metrics.py`)**:
  - Thread-safe `Counter`, `Gauge`, and `Histogram` with customizable latency buckets.
  - Metrics tracking order lifecycle, execution latency, pre-trade risk duration, market tick staleness (<3000ms), reconciliation drift, active live sessions, and HTTP traffic.
  - Raw OpenMetrics text generation exposed at `/metrics`.
- **OpenTelemetry Distributed Tracing & Correlation Middleware (`src/openquant/adapters/observability/telemetry.py`, `src/openquant/interfaces/api/middleware/correlation.py`)**:
  - `correlation_id_ctx` tracking `X-Correlation-ID` across coroutine boundaries.
  - `trace_span` context manager for capturing spans, duration, and error details.
  - `InMemoryTraceCollector` circular buffer for real-time span analysis.
- **Observability Application Service & REST API (`src/openquant/application/services/observability_service.py`, `src/openquant/interfaces/api/v1/endpoints/observability.py`)**:
  - `GET /metrics`: Prometheus scraping endpoint.
  - `GET /api/v1/observability/summary`: System telemetry metrics JSON.
  - `GET /api/v1/observability/traces`: Query distributed trace spans and timings.
  - `GET /api/v1/observability/dashboards`: Grafana dashboard template registry.
- **Grafana Dashboards Suite (`deployments/grafana/dashboards/`)**:
  - `trading-operations.json`: Order rate by status and p95/p99 execution latency.
  - `risk-controls.json`: Kill switch status, pre-trade hard stop evaluations & breach rate.
  - `market-data-latency.json`: 3000ms staleness monitoring and tick ingestion volume.
- **Frontend Observability Console (`frontend/src/features/observability/ObservabilityPage.tsx`)**:
  - Real-time telemetry cards, trace span inspector with correlation ID search, live Prometheus `/metrics` exporter view, and 1-click Grafana JSON export.

---

## [0.19.0] - Milestone 19: Live Trading Mode

### Added
- **Live Trading Domain Models & Ports (`src/openquant/domain/models/live_trading.py`, `src/openquant/domain/ports/live_trading_port.py`)**:
  - `LiveTradingState`, `ScalingTier` (Starter 25%, Intermediate 50%, Full 100%), `LiveCapitalAllocation`, `LivePreflightReport`, `LiveStrategySession`.
  - `ILiveSessionRepository`, `ILiveTradingService`.
- **Automated 5-Point Preflight Verification Matrix (Non-Negotiable Guardrails)**:
  - Stage 4 Promotion Gate verification (Rule 1).
  - Automated 5-point sandbox audit certification for broker adapters (Rule 9).
  - Pre-trade risk engine state & kill switch unlocked verification (Rules 2 & 4).
  - 3000ms market data staleness threshold verification (Rule 7).
  - Broker authenticated session handshake verification.
- **Live Trading Application Service (`src/openquant/application/services/live_trading_service.py`)**:
  - Orchestration of preflight checks, dual-operator session activation, gradual position scaling, and emergency halting.
  - Event bus emission (`live_trading.activated`, `live_trading.scaled`, `live_trading.halted`) and audit logging.
- **Live Trading REST API (`src/openquant/interfaces/api/v1/endpoints/live_trading.py`)**:
  - `POST /api/v1/live-trading/preflight`, `POST /api/v1/live-trading/sessions`, `GET /api/v1/live-trading/sessions`, `GET /api/v1/live-trading/sessions/{id}`, `POST /api/v1/live-trading/sessions/{id}/scale`, `POST /api/v1/live-trading/sessions/{id}/halt`.
- **Frontend Live Trading Mission Control (`frontend/src/features/live-trading/LiveTradingConsolePage.tsx`)**:
  - Real-time preflight matrix visualizer with pass/fail status badges.
  - Capital allocation & gradual position scaling calculator.
  - Dual confirmation verification modal.
  - Active session telemetry cards with live PnL, filled orders count, and 1-click **Emergency Halt**.

---

## [0.18.0] - Milestone 18: Additional Broker Adapters

### Added
- **Interactive Brokers Adapter (`src/openquant/adapters/brokers/interactive_brokers_adapter.py`)**:
  - TWS & IB Gateway client supporting multi-asset contracts (Equities, Futures, Options, Forex, Bonds, Commodities).
  - TWS tiered commission modeling ($1 min), simulated execution fills, and margin account reporting.
- **Angel One SmartAPI Adapter (`src/openquant/adapters/brokers/angelone_adapter.py`)**:
  - TOTP authentication handshake and JWT session management.
  - NSE/NFO order routing, DP holding queries, and flat fee structure.
- **Binance Crypto Adapter (`src/openquant/adapters/brokers/binance_adapter.py`)**:
  - HMAC-SHA256 authenticated REST and WebSocket connectivity for Spot and USDT-M Perpetual Futures.
  - Multi-asset collateral management and maker/taker trading fee calculation.
- **Broker Adapter Registry Integration (`src/openquant/adapters/brokers/registry.py`)**:
  - Default registry seeded with all 5 certified broker adapters.
- **Automated Certification & Security Review Harness (Rule 9)**:
  - 100% pass rate across the 5-point harness (`CREDENTIAL_LEAKAGE_AUDIT`, `AUTH_HANDSHAKE_VALIDATION`, `SANDBOX_ORDER_LIFECYCLE`, `POSITIONS_AND_FUNDS_INTEGRITY`, `FAULT_TOLERANCE_AND_SHUTDOWN`).
- **Frontend Broker Adapters UI (`frontend/src/features/brokers/BrokerAdaptersPage.tsx`)**:
  - Dynamic multi-currency display (`$`, `₹`, `₮`), live server synchronization, and 1-click audit execution.

---

## [0.17.0] - Milestone 17: Notification System & Event Bus

### Added
- **Notification Domain Models & Ports (`src/openquant/domain/models/notification.py`, `src/openquant/domain/ports/notification_port.py`)**:
  - `NotificationChannelConfig`, `NotificationMessage`, `NotificationChannelType`, `NotificationSeverity`, `NotificationStatus`, `PlatformEvent`.
  - `IEventBus`, `INotificationDispatcher`, `INotificationChannelRepository`, `INotificationLogRepository`.
- **Event Bus & Notification Dispatcher Adapters (`src/openquant/adapters/event_bus/`, `src/openquant/adapters/notifications/`)**:
  - `InMemoryEventBus` with topic and wildcard publish-subscribe pattern matching.
  - `NotificationDispatcher` supporting Telegram bot API, Discord rich webhook embeds, SMTP Email, signed HTTP Webhooks, and In-App delivery.
  - Automated connectivity test ping runner (`test_channel`).
- **Notification Application Service (`src/openquant/application/services/notification_service.py`)**:
  - Channel CRUD, manual broadcast alerting, unread in-app counter, and automated event subscriptions (`risk.kill_switch`, `risk.breach`, `reconciliation.mismatch`, `market_data.stale`).
- **Notification REST API (`src/openquant/interfaces/api/v1/endpoints/notifications.py`)**:
  - `GET /api/v1/notifications/channels`, `POST /api/v1/notifications/channels`, `PUT /api/v1/notifications/channels/{id}`, `DELETE /api/v1/notifications/channels/{id}`, `POST /api/v1/notifications/channels/{id}/test`, `POST /api/v1/notifications/broadcast`, `GET /api/v1/notifications/logs`, `GET /api/v1/notifications/in-app`, `POST /api/v1/notifications/in-app/{id}/read`.
- **Frontend Notification Center UI (`frontend/src/features/notifications/NotificationCenterPage.tsx`)**:
  - Active channels counter, 24h dispatched log metrics, and unread in-app alerts.
  - Configured channels table with 1-click Test Ping buttons.
  - Modal to register Discord, Telegram, Email, and Webhook channels.
  - Manual broadcast dispatcher and interactive in-app alert feed.

---

## [0.16.0] - Milestone 16: Portfolio Management & Analytics

### Added
- **Portfolio Domain Models & Ports (`src/openquant/domain/models/portfolio.py`, `src/openquant/domain/ports/portfolio_port.py`)**:
  - `PortfolioPosition`, `AssetAllocationItem`, `PortfolioPerformanceSnapshot`, `PortfolioSummary`.
  - `IPortfolioAnalyticsEngine` defining contracts for mark-to-market valuation, asset allocation, and equity curve analytics.
- **Portfolio Analytics Engine Adapter (`src/openquant/adapters/portfolio/portfolio_analytics_engine.py`)**:
  - Mark-to-market position tracking against live market feeds.
  - Multi-asset exposure percentage calculations and concentration risk analysis.
  - Historical equity curve snapshots with peak watermark and drawdown tracking (Rule 2).
- **Portfolio Application Service (`src/openquant/application/services/portfolio_service.py`)**:
  - Coordinates multi-account analytics retrieval and OMS 1-click position flattening with audit logs.
- **Portfolio REST API (`src/openquant/interfaces/api/v1/endpoints/portfolio.py`)**:
  - `GET /api/v1/portfolio/summary`, `GET /api/v1/portfolio/positions`, `GET /api/v1/portfolio/allocation`, `GET /api/v1/portfolio/performance`, `POST /api/v1/portfolio/positions/{symbol}/close`.
- **Frontend Portfolio Management UI (`frontend/src/features/portfolio/PortfolioManagementPage.tsx`)**:
  - Real-time NAV, cash balance, unrealized PnL, margin utilization, and Sharpe ratio stat cards.
  - Active positions table with 1-click market order close action.
  - Asset allocation & concentration risk progress meters (30% limit threshold).
  - 14-day historical equity trajectory and drawdown depth visualizer.

---

## [0.15.0] - Milestone 15: AI Advisory Suite

### Added
- **AI Advisory Domain Models & Ports (`src/openquant/domain/models/ai_advisory.py`, `src/openquant/domain/ports/ai_advisory_port.py`)**:
  - `AICodeGenerationRequest`, `AICodeGenerationResult`, `AIReviewStatus` enforcing Non-Negotiable Rule 3.
  - `AILogAnalysisReport`, `AIAnomalyItem`, `AIRiskAdviceReport`, `AIRiskRecommendation`.
- **AI Advisory Engine Adapter (`src/openquant/adapters/ai/ai_advisory_engine.py`)**:
  - Synthesizes `BaseStrategy` Python quant code verified with `ASTSecurityValidator`.
  - Analyzes audit telemetry to detect pre-trade risk clusters, staleness alerts, and emergency halts.
  - Generates explainable risk diagnostics and remediation recommendations.
- **AI Advisory Application Service (`src/openquant/application/services/ai_advisory_service.py`)**:
  - Coordinates generation, mandatory human review workflow (`approve_generated_code`), log analysis, and risk explanation.
- **AI Advisory REST API (`src/openquant/interfaces/api/v1/endpoints/ai_advisory.py`)**:
  - `POST /api/v1/ai/generate-strategy`, `POST /api/v1/ai/approve/{generation_id}`, `POST /api/v1/ai/analyze-logs`, `POST /api/v1/ai/explain-risk`.
- **Frontend AI Advisory Suite UI (`frontend/src/features/ai-advisory/AIAdvisorySuitePage.tsx`)**:
  - Quant Strategy Code Generator with AST Compliance Badge and Human Approval action.
  - Log & Telemetry Anomaly Scanner with health score gauge and root-cause breakdown.
  - Explainable Risk Advisor with natural language breach translation.

---

## [0.14.0] - Milestone 14: Additional Strategy Sources

### Added
- **TradingView Alert Webhook Handler (`src/openquant/adapters/sources/tradingview_webhook.py`)**:
  - HMAC-SHA256 signature verification over canonical payload or HTTP header.
  - Replay attack defense with memory-cached nonces and $\le 60\text{s}$ TTL clock skew checks.
  - Direct routing into pre-trade risk evaluation (Rules 2, 4, 7, 8) before OMS execution.
- **MetaTrader 5 ZeroMQ Socket Bridge Adapter (`src/openquant/adapters/sources/mt5_bridge.py`)**:
  - High-throughput ZeroMQ IPC socket adapter for EA command dispatch, tick streaming, and heartbeat monitoring.
- **Structured Google Sheets / CSV Parser (`src/openquant/adapters/sources/sheets_parser.py`)**:
  - Typed row parsing with validation diagnostics and batch OMS order execution.
- **Strategy Sources REST API (`src/openquant/interfaces/api/v1/endpoints/strategy_sources.py`)**:
  - `POST /api/v1/sources/tradingview/webhook`, `GET /api/v1/sources/mt5/status`, `POST /api/v1/sources/mt5/command`, `POST /api/v1/sources/sheets/parse`, `POST /api/v1/sources/sheets/execute`.
- **Frontend Strategy Sources UI (`frontend/src/features/sources/StrategySourcesPage.tsx`)**:
  - Webhook configurator & test alert dispatcher, MT5 telemetry status monitor, and CSV syntax validation table.

---

## [0.13.0] - Milestone 13: State Reconciliation Engine

### Added
- **State Reconciliation Engine (`src/openquant/adapters/reconciliation/state_reconciliation_engine.py`)**:
  - Implements `IReconciliationEngine` port for scheduled and on-demand OMS vs Broker actuals reconciliation.
  - Granular drift detection: `QUANTITY_MISMATCH`, `PHANTOM_INTERNAL`, `PHANTOM_BROKER`, `PRICE_MISMATCH`.
  - Rule 5 Emergency Auto-Halt Interlock activating Platform Kill Switch on discrepancy detection.
  - Manual one-click force synchronization (`sync_positions_from_broker`).
- **Reconciliation Application Service (`src/openquant/application/services/reconciliation_service.py`)**:
  - Pre-order consistency verification hook (`pre_order_reconciliation_check`).
  - Immutable compliance logging for reconciliation runs, auto-halts, and force-sync events.
- **Reconciliation REST API (`src/openquant/interfaces/api/v1/endpoints/reconciliation.py`)**:
  - `POST /api/v1/reconciliation/run`, `POST /api/v1/reconciliation/accounts/{id}/run`, `GET /api/v1/reconciliation/reports`, `GET /api/v1/reconciliation/reports/{id}`, `POST /api/v1/reconciliation/accounts/{id}/sync`.
- **Frontend State Reconciliation UI (`frontend/src/features/reconciliation/StateReconciliationPage.tsx`)**:
  - Reconciliation health overview scorecards, Account control bar, Position Discrepancy Matrix with severity badges, and Historical Runs audit list.

---

## [0.12.0] - Milestone 12: Paper Trading Mode

### Added
- **Real-Time Paper Trading Mode Engine (`src/openquant/adapters/paper/paper_trading_engine.py`)**:
  - Implements `IPaperTradingEngine` port for live simulated execution against broker feeds.
  - Latency simulation (50–200ms) and slippage modeling (configurable bps).
  - Virtual Paper Accounts (`PaperAccount`) with marked-to-market balances and margin tracking.
  - Active Paper Session event loop processing live ticks with `process_market_tick`.
- **Stage 5 Promotion Gate Checklist & Compliance (`PaperTradingGateStatus`)**:
  - Validates minimum 14 active days, 30 executed trades, and maximum 10.0% drawdown.
  - Stage 5 (`PAPER_TRADING`) to Stage 6 (`HUMAN_APPROVAL`) promotion workflow.
- **Paper Trading Application Service (`src/openquant/application/services/paper_trading_service.py`)**:
  - Session lifecycle management (start, pause, stop) and Stage 6 gate promotion.
  - Immutable compliance audit logging.
- **Paper Trading REST API (`src/openquant/interfaces/api/v1/endpoints/paper_trading.py`)**:
  - `POST /api/v1/paper-trading/accounts`, `GET /api/v1/paper-trading/accounts`, `POST /api/v1/paper-trading/sessions`, `GET /api/v1/paper-trading/sessions`, `GET /api/v1/paper-trading/sessions/{session_id}`, `POST /api/v1/paper-trading/sessions/{session_id}/pause`, `POST /api/v1/paper-trading/sessions/{session_id}/stop`, `GET /api/v1/paper-trading/sessions/{session_id}/gate-status`, `POST /api/v1/paper-trading/sessions/{session_id}/promote`.
- **Frontend Paper Trading UI (`frontend/src/features/paper-trading/PaperTradingPage.tsx`)**:
  - Virtual Account balance scorecards, active paper sessions table with pause/stop controls, launch session modal, and Stage 5 Promotion Gate checklist card.

---

## [0.11.0] - Milestone 11: Backtesting Engine & Walk-Forward Validation

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
