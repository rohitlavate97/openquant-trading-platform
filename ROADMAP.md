# OpenQuant Engineering Roadmap

Progress and milestone tracker for the OpenQuant Algorithmic Trading Platform.

| Milestone | Title | Status | Scope / Core Deliverables |
|:---:|---|:---:|---|
| **01** | **Project Setup & Hexagonal Boundaries** | 🟢 **Completed** | Repository scaffolding, Docker, CI, clean architecture ports & adapters skeleton, structural boundary tests, Sandbox AST security validator, and initial React dashboard with Kill Switch. |
| **02** | **Authentication, RBAC & Secrets Management** | 🟢 **Completed** | JWT authentication, bcrypt password hashing, multi-tenant RBAC permissions, encrypted secrets vault (AES/Fernet PBKDF2), programmatic API keys, and Frontend Vault UI. |
| **03** | **Database Foundation & Audit Logging** | 🟢 **Completed** | Async SQLAlchemy 2.x ORM models, Alembic migrations, idempotency indexes, append-only audit log repository, and Frontend Audit Trail Viewer. |
| **04** | **Broker Adapter Interface & First Adapter** | 🟢 **Completed** | Standardized `IBrokerAdapter` multi-broker port, high-fidelity `PaperBrokerAdapter`, `ZerodhaKiteAdapter`, automated 5-check `BrokerAdapterCertificationHarness`, and Broker Management UI. |
| **05** | **Unified REST & WebSocket Layer** | 🟢 **Completed** | Multiplexed `WebSocketConnectionManager`, real-time streams (`/ws/v1/market-data`, `/ws/v1/orders`, `/ws/v1/telemetry`), `StreamingBroadcasterService`, and React `LiveMarketTicker`. |
| **06** | **Market Data Ingestion & Staleness Engine** | 🟢 **Completed** | `InMemoryMarketDataFeed`, `StreamingCandleAggregator` (OHLCV 1m-1d), `SyntheticMarketFeed`, pre-trade 3000ms staleness guard (Rule 7), and `MarketDataManagementPage`. |
| **07** | **Order Management System (OMS)** | 🟢 **Completed** | Strict idempotency engine (Rule 8), state machine lifecycle, weighted average entry price, realized/unrealized PnL, position reconciliation, and `OrderManagementPage`. |
| **08** | **Risk Engine & Global Kill Switch** | 🟢 **Completed** | Synchronous pre-trade hard stops (daily loss %, max drawdown, position sizing, rate limit, self-trade), 1-click Global Kill Switch, and `RiskManagementPage`. |
| **09** | **Strategy Execution Sandbox** | 🟢 **Completed** | Resource quotas (512MB RAM, 30s CPU limit, timeouts), AST static analysis, safe module allowlisting, print redirection, and `StrategySandboxPage`. |
| **10** | **Strategy Engine (Python Source)** | 🟢 **Completed** | Python strategy runtime funneled through Sandbox → Backtest → Paper, lifecycle hooks (`on_start`, `on_bar`, `on_tick`, `on_stop`), and `StrategyManagementPage`. |
| **11** | **Backtesting Engine & Walk-Forward Validation**| 🟢 **Completed** | Historical event-driven simulation, slippage & commission models, equity curve, Sharpe, Sortino, max drawdown, and Out-of-Sample Walk-Forward efficiency validation. |
| **12** | **Paper Trading Mode** | 🟢 **Completed** | Real-time simulated execution against broker sandbox feeds, simulated latency & slippage, virtual accounts, and Stage 5 promotion gating. |
| **13** | **State Reconciliation Engine** | 🟢 **Completed** | Scheduled and pre-order mismatch detection against broker actuals; auto-halt kill-switch interlock on discrepancy (Rule 5). |
| **14** | **Additional Strategy Sources** | 🟢 **Completed** | Signed TradingView webhooks (HMAC-SHA256 & replay nonce protected), MT5 ZeroMQ bridge, structured Sheets CSV parser, and Strategy Sources UI. |
| **15** | **AI Advisory Suite** | 🟢 **Completed** | Assistant, AST-verified code generator (mandatory human review Rule 3), telemetry log analyzer, and explainable risk advisor. |
| **16** | **Portfolio Management & Analytics** | 🟢 **Completed** | Multi-account position tracking, mark-to-market valuations, asset allocation breakdown, equity & drawdown curves, and OMS 1-click position flattening. |
| **17** | **Notification System & Event Bus** | ⚪ Pending | Multi-channel alerting (Telegram, Discord, Email), event-driven scheduler. |
| **18** | **Additional Broker Adapters** | ⚪ Pending | Interactive Brokers, Angel One, Binance/Crypto (certified independently). |
| **19** | **Live Trading Mode** | ⚪ Pending | Capital allocation controls, gradual position scaling, rigorous pre-requisite verification. |
| **20** | **Observability & Monitoring** | ⚪ Pending | Prometheus metrics, Grafana dashboards, Loki log aggregation, OpenTelemetry traces. |
| **21** | **Security Hardening & Load Testing** | ⚪ Pending | Penetration testing, sandbox escape tests, stress testing order pipelines. |
| **22** | **Production Deployment** | ⚪ Pending | Production Docker images, Kubernetes helm charts, self-hosting deployment guide. |
