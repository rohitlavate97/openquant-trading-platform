# OpenQuant Engineering Roadmap

Progress and milestone tracker for the OpenQuant Algorithmic Trading Platform.

| Milestone | Title | Status | Scope / Core Deliverables |
|:---:|---|:---:|---|
| **01** | **Project Setup & Hexagonal Boundaries** | 🟢 **In Progress** | Repository scaffolding, Docker, CI, clean architecture ports & adapters skeleton, structural boundary tests, Sandbox AST security validator, and initial React dashboard with Kill Switch. |
| **02** | **Authentication, RBAC & Secrets Management** | ⚪ Pending | JWT auth, OAuth2, multi-tenant RBAC, encrypted broker credential vault. |
| **03** | **Database Foundation & Audit Logging** | ⚪ Pending | Async SQLAlchemy ORM, Alembic migrations, immutable audit log tables. |
| **04** | **Broker Adapter Interface & First Adapter** | ⚪ Pending | Abstract adapter interface, sandbox testing harness, Zerodha/Paper adapter certification. |
| **05** | **Unified REST & WebSocket Layer** | ⚪ Pending | Standardized REST API & WebSocket streams over the adapter layer. |
| **06** | **Market Data Ingestion & Staleness Engine** | ⚪ Pending | Real-time tick & candle processing, fail-safe disconnect pause, staleness detection. |
| **07** | **Order Management System (OMS)** | ⚪ Pending | Idempotent order processing, order lifecycle state machine, duplicate prevention. |
| **08** | **Risk Engine & Global Kill Switch** | ⚪ Pending | Synchronous pre-trade hard stops (daily loss %, max drawdown, position sizing), synchronous Kill Switch. |
| **09** | **Strategy Execution Sandbox** | ⚪ Pending | Resource quotas (CPU/RAM/time), restricted execution environment, AST static analysis. |
| **10** | **Strategy Engine (Python Source)** | ⚪ Pending | Python strategy runtime funneled through Sandbox → Backtest → Paper. |
| **11** | **Backtesting Engine & Walk-Forward Validation**| ⚪ Pending | Historical event-driven simulation, out-of-sample walk-forward efficiency metrics. |
| **12** | **Paper Trading Mode** | ⚪ Pending | Real-time simulated execution against broker sandbox feeds. |
| **13** | **State Reconciliation Engine** | ⚪ Pending | Scheduled and pre-order mismatch detection against broker actuals; auto-halt on discrepancy. |
| **14** | **Additional Strategy Sources** | ⚪ Pending | Signed TradingView webhooks (replay-protected), MT5 bridge, structured Sheets parser. |
| **15** | **AI Advisory Suite** | ⚪ Pending | Assistant, code generator (mandatory human review), log analyzer, explainable risk advisor. |
| **16** | **Portfolio Management & Analytics** | ⚪ Pending | Holdings, position tracking, PnL analytics, drawdown metrics. |
| **17** | **Notification System & Event Bus** | ⚪ Pending | Multi-channel alerting (Telegram, Discord, Email), event-driven scheduler. |
| **18** | **Additional Broker Adapters** | ⚪ Pending | Interactive Brokers, Angel One, Binance/Crypto (certified independently). |
| **19** | **Live Trading Mode** | ⚪ Pending | Capital allocation controls, gradual position scaling, rigorous pre-requisite verification. |
| **20** | **Observability & Monitoring** | ⚪ Pending | Prometheus metrics, Grafana dashboards, Loki log aggregation, OpenTelemetry traces. |
| **21** | **Security Hardening & Load Testing** | ⚪ Pending | Penetration testing, sandbox escape tests, stress testing order pipelines. |
| **22** | **Production Deployment** | ⚪ Pending | Production Docker images, Kubernetes helm charts, self-hosting deployment guide. |
