# Master Prompt v2 — Enterprise Open-Source Algorithmic Trading Platform (OpenQuant)

## Role

You are acting as a **Principal Software Architect, Quant Developer, DevOps Engineer, Backend Engineer, Frontend Engineer, Security Engineer, and QA Lead** — think like a staff engineer at Google, Meta, or Amazon.

Build a **production-grade, enterprise-level, open-source algorithmic trading platform** comparable to OpenAlgo, but with better architecture, scalability, security, AI integration, and developer experience. **This platform will be self-hosted by thousands of traders and will place real orders with real brokers using real capital once Live Trading is enabled.** Every requirement below treats that as the first fact to design around, not a feature to bolt on later.

---

## Non-Negotiable Operating Rules (Capital-Safety Rules Come First)

1. **No strategy — regardless of source (Python, TradingView webhook, MT5, Excel/Sheets, REST/WebSocket, or AI-generated) — may place a live order without first passing Backtesting, Walk-Forward Validation, and a configured minimum period of Paper Trading meeting explicit promotion criteria.** There is no code path, and no strategy source, that skips this (see Strategy Promotion Gate).
2. **Live Trading is disabled by default, per strategy, per account, per broker connection.** Enabling it is an explicit, separate, human-performed action — never a side effect of a strategy "looking good" in backtest.
3. **A global Kill Switch is reachable within one action from anywhere in the UI and immediately halts all order placement**, optionally flattening open positions. Tested as rigorously as core trading logic.
4. **Daily Loss Limit and Max Drawdown are hard stops enforced by the Risk Engine before order placement — not advisory dashboard numbers.** Once breached, new orders are blocked for that strategy/account until manually reset.
5. **Every order is idempotent**, checked against an idempotency key before submission — a retried request never produces a duplicate live order.
6. **The platform reconciles internal position/order state against each connected broker's actual account state on a defined schedule and before any new order placement.** A detected mismatch halts trading for that account until resolved.
7. **All user-submitted and AI-generated strategy code executes inside an isolated Strategy Execution Sandbox** (see Strategy Execution Security) — never with direct filesystem, network, or host-process access beyond the platform's declared, mediated broker/data interfaces.
8. **AI-generated strategy code is never auto-deployed.** It passes through the same Strategy Promotion Gate as human-written code, with no shortcut — "the AI wrote it" is never a reason to skip backtesting, sandboxed execution review, or human approval.
9. **Every broker adapter — first-party or community-contributed — is validated against that broker's sandbox/paper environment and passes a security review before being eligible for Live Trading.** An adapter is a trusted, privileged component (it handles credentials and places real orders); it is never trusted merely because it compiles.
10. **TradingView webhooks and any external REST/WebSocket strategy trigger are authenticated, signed, and replay-protected** — an unauthenticated or replayed webhook must never be able to trigger a real order.
11. **Never generate placeholder code**, especially not in the Order Management System, Risk Engine, or reconciliation logic — these modules are where "TODO, fix later" means "this can lose money."
12. **Build one milestone at a time, exactly as your original process specifies**: design the complete architecture, break into milestones, implement one at a time, verify with tests, refactor, keep docs updated, never move to the next milestone until the current one is production-ready.
13. **Every commit is pushed to a remote feature branch** as part of the commit workflow (see Git & Commit-Wise Development).

---

## Strategy Promotion Gate (Mandatory Lifecycle — Applies to Every Strategy Source Uniformly)

```
Draft → Sandboxed Code Review → Backtest → Walk-Forward Validation
   → Paper Trading (minimum duration + performance criteria) → Human Approval
   → Live Trading (small size / gradual increase) → Full Live
```

- This applies identically whether the strategy arrived as Python code, a TradingView webhook config, an MT5 bridge script, an Excel/Sheets rule set, or AI-generated code — **the gate does not have a fast path for any source.**
- Promotion criteria (minimum Sharpe/Sortino threshold, minimum paper-trading duration, maximum acceptable drawdown observed in paper trading) are configured explicitly, not left to judgment at build time.
- Automatic demotion: a live strategy breaching its configured risk limits is immediately demoted to Paper Trading or halted; a human must re-approve promotion.
- Every promotion/demotion event is logged with its triggering reasoning and metrics.

---

## Strategy Execution Security (Mandatory — the Risk Your Original Brief Doesn't Yet Address)

Supporting Python strategies, Excel/Google Sheets rule sources, and **AI code generation** means this platform will execute code it did not write and cannot fully trust by default. This is treated as a first-class security concern, not an implementation detail:

- **Strategy Execution Sandbox:** every strategy (Python code, AI-generated code, or a rule-set compiled from Excel/Sheets) runs in an isolated, resource-limited environment (container or restricted interpreter) with a strict allowlist of capabilities — it may call the platform's mediated market-data/order-submission interfaces and nothing else. No arbitrary filesystem access, no arbitrary outbound network calls, no host-process access.
- **Resource limits are enforced**, not assumed: CPU time, memory, and execution-time budgets per strategy invocation, with a runaway strategy killed and flagged rather than allowed to degrade the platform for other users.
- **Excel/Google Sheets strategies are parsed as structured rule definitions, never executed as live macros/scripts** — embedded macros in an uploaded spreadsheet are stripped/ignored, not run, since spreadsheet macros are a well-known malware vector.
- **AI-generated code is presented to the user for review before it ever enters the sandbox for backtesting** — the AI assistant drafts, a human reads and approves the actual code, consistent with this platform family's human-in-the-loop principle applied to code generation specifically.
- **Static analysis / linting for dangerous patterns** (e.g., `eval`, `exec`, dynamic imports, network calls to non-allowlisted hosts) runs on every submitted strategy — Python, AI-generated, or otherwise — before it's accepted into the sandbox at all.

---

## Broker Adapter Security (Mandatory, Given Open-Source/Community Contribution)

- **The Adapter Pattern interface is the *only* way the rest of the system reaches a broker** — the OMS, Risk Engine, and every strategy source depend on the adapter interface, never a broker SDK directly.
- **Every adapter is validated against its broker's sandbox/paper environment** and passes a security review (credential handling, no unexpected outbound calls, correct error handling) before being marked "Live-Trading eligible" in the adapter registry.
- **Community-contributed adapters go through the same certification path as first-party ones** — an open-source platform's biggest supply-chain risk is a broker adapter that mishandles credentials or has a latent bug; this is treated as seriously as the OMS itself, not as "just a plugin."
- **Broker credentials are the platform's most sensitive secret** — stored via a proper secrets manager, encrypted, scoped per user/account, never logged, instantly revocable.

---

## Functional Architecture

**Multi-broker architecture** behind the Adapter Pattern (login, refresh token, place/modify/cancel order, order history, positions, holdings, funds, quotes, historical data, WebSocket, instrument download) — the rest of the system never knows which broker is in use.

**Unified REST API + Unified WebSocket** over the adapter layer.

**Order Management System (OMS):** the single, idempotent, reconciled order path every strategy source funnels through — no strategy source has a side channel to broker order placement that bypasses the OMS or the Risk Engine.

**Portfolio Management, Position Tracking, Holdings, Funds:** built on the same reconciled state the OMS maintains.

**Risk Engine:** the single pre-trade, synchronous, blocking check every order passes through (per Non-Negotiable Rule 4) — daily loss limits, max drawdown, position/exposure limits, margin checks.

**Strategy Engine:** supports Python, TradingView Webhooks, MetaTrader 5, Excel, Google Sheets, REST API, and WebSocket as strategy sources — **all normalized into one internal strategy representation and funneled through the same Strategy Promotion Gate, Strategy Execution Sandbox, OMS, and Risk Engine**, regardless of source.

**Signal Processing, Paper Trading, Live Trading, Backtesting, Historical Replay, Market Data, Scheduler, Event Bus, Plugin System, Notification System, User Management (multi-user, multi-account, API keys), Logs, Monitoring, Analytics Dashboard** — all as specified in your original brief, built on top of the shared OMS/Risk Engine/Sandbox core rather than as parallel, independently-implemented paths.

---

## AI Features (Advisory Only — Consistent With This Platform Family's Trading Prompts)

- **AI strategy assistant:** proposes strategy logic; produces a Draft-stage strategy only, never live.
- **AI code generation:** drafts strategy code for human review before it enters the sandbox (per Strategy Execution Security).
- **AI debugging:** explains likely causes of a strategy error or unexpected backtest result, grounded in the actual logs/backtest output, not generic guesses.
- **AI log analysis:** summarizes and flags anomalies in real logs — every claim traceable to an actual log line, never invented.
- **AI risk explanation:** explains *why* the Risk Engine blocked or flagged something, in plain language, grounded in the actual triggering rule/metric.
- **AI trade journal:** reflects the trader's own recorded trades and notes back to them, encouraging their own review — it does not diagnose or label the trader's psychology, consistent with this platform family's standard for journaling features.
- **AI documentation:** generates/updates developer and user docs from the actual codebase, not aspirational descriptions of unbuilt features.

No AI feature above has order-placement authority. All of them assist a human; none of them act unsupervised.

---

## Technology Stack

**Backend:** Python 3.13, FastAPI, HTTPX, SQLAlchemy 2.x (async), PostgreSQL, Redis, Celery, WebSockets, Pydantic v2, Alembic
**Frontend:** React, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query, Zustand
**Infrastructure:** Docker, Docker Compose, GitHub Actions, Nginx, Prometheus, Grafana, Loki, OpenTelemetry
**Security:** JWT, OAuth2, RBAC, CSRF protection, rate limiting, audit logging, secrets management
**Testing:** Pytest, Playwright, Vitest

---

## System Architecture

Clean Architecture, DDD, SOLID, DRY, KISS, Twelve-Factor App principles. Every design decision justified with stated trade-offs before implementation. The Adapter Pattern (brokers) and a matching port/adapter boundary around strategy execution (the Sandbox) are the two hexagonal boundaries this platform is built around — the domain layer (OMS, Risk Engine, Strategy Promotion Gate logic) never imports a specific broker SDK or a specific strategy-source parser directly, proven by a structural import-boundary test.

---

## Real-Time Architecture (Mandatory — Genuinely Critical, Same Bar as This Family's Other Trading Platforms)

- **Live market data:** persistent WebSocket connections per broker, with staleness detection — a strategy never acts on a price older than a configured freshness threshold.
- **Reconnection strategy tested:** on feed disconnection, dependent strategies pause new order placement immediately (fail-safe), resuming only once the feed is confirmed fresh.
- **Order execution/status updates** push to the frontend via WebSocket the moment they happen, with measured latency.
- **Risk Engine evaluation is synchronous and pre-trade**, in the order-placement path itself — never eventually-consistent.
- **Reconciliation** runs on a defined schedule and pushes results live to the dashboard.

---

## Security

HTTPS, JWT authentication, RBAC, rate limiting, CSRF protection, CORS, session management, encryption at rest, secure secrets management, full audit trail — plus, specific to this platform: **Strategy Execution Sandbox isolation**, **broker adapter certification**, and **webhook/API strategy-trigger authentication with replay protection** (per Non-Negotiable Rule 10), since these are this platform's distinguishing attack surfaces beyond generic web-app security.

---

## Observability

Structured logging, distributed tracing (OpenTelemetry), metrics (Prometheus/Grafana), health checks, performance dashboards, latency monitoring, error reporting (Loki) — with dedicated dashboards for Risk Engine trigger rates, sandbox resource-limit violations, and broker-adapter error rates, since those are the signals that matter most for this specific platform's safety posture.

---

## Testing

Pytest, Playwright, Vitest, plus the trading-specific categories this platform family requires as non-negotiable:
- **Idempotency tests:** retried/duplicate order requests produce exactly one order
- **Reconciliation tests:** a broker/internal state mismatch halts trading for that account
- **Kill Switch tests:** immediate halt of all order placement
- **Risk-limit enforcement tests:** orders blocked (not just flagged) once limits are breached
- **Walk-forward validation tests:** no strategy promotes past Backtest using in-sample metrics alone
- **Sandbox escape tests:** a strategy attempting filesystem/network access outside its allowlist is blocked and flagged
- **Static-analysis tests:** dangerous code patterns (`eval`, `exec`, non-allowlisted network calls) are caught before a strategy enters the sandbox
- **Webhook security tests:** unauthenticated or replayed webhook requests are rejected
- **Broker adapter certification tests:** each adapter tested against its broker's sandbox before Live-Trading eligibility
- Target high coverage on OMS, Risk Engine, Strategy Execution Sandbox, and reconciliation specifically — the modules where "good enough" isn't

---

## Deliverables (Per Module, As Your Original Specifies)

Architecture diagram, folder structure, database schema, API specification, sequence diagrams, production-ready implementation, unit tests, integration tests, documentation, deployment guide.

---

## Git & Commit-Wise Development (Mandatory)

### Branching Strategy
- `main` — always deployable; nothing committed directly.
- One **feature branch per milestone**, named `milestone-<number>-<short-name>` (e.g., `milestone-07-risk-engine-hard-stops`).
- Push to remote when a milestone's tests pass and it's genuinely production-ready; describe a PR against `main`; merge waits for explicit approval. **Any milestone touching the OMS, Risk Engine, Strategy Execution Sandbox, or broker adapters requires an explicit PR statement of what was tested and how**, beyond the standard template.

### Per-Commit Process
Sequential commit number, Conventional Commit message, business/technical objective, architectural decisions and trade-offs, database changes, backend changes, frontend changes, code for that commit only, tests (including any trading-specific or sandbox-security category relevant to it), documentation updates, manual verification steps, **commit locally then push the milestone branch to remote**, **stop and wait for explicit approval before the next commit.**

- Maintain a running **`CHANGELOG.md`** and an up-to-date **project roadmap**, updated after every completed feature per your original process.
- **Tag major milestones on `main` after merge** (e.g., `v0.1-broker-adapter-layer`, `v0.4-backtesting-engine`, `v0.7-risk-engine-and-sandbox`, `v1.0-live-trading-enabled`).
- `.gitignore` excludes `.env`, credentials, virtual environments, build artifacts. **No real broker credentials, sandbox or otherwise, are ever committed.**

### Milestone Roadmap (Build Strictly in This Order — Live Trading Is Explicitly Last)

1. Project setup (repo structure, Docker, CI, remote repo + branching convention, hexagonal boundary skeleton for Adapter Pattern and Strategy Sandbox)
2. Authentication, RBAC, secrets management foundation
3. Database foundation + audit-log design
4. Broker Adapter interface + first adapter (sandbox-validated, security-reviewed)
5. Unified REST API + WebSocket over the adapter layer
6. Market data ingestion (WebSocket feeds, staleness detection)
7. Order Management System (idempotent, reconciled) — built and proven before any strategy source can reach it
8. Risk Engine (pre-trade hard-stop enforcement, Kill Switch) — built before Live Trading capability exists anywhere
9. Strategy Execution Sandbox (isolation, resource limits, static analysis) — built before any strategy source is wired in
10. Strategy Engine: Python source first, funneled through Sandbox → Backtest → Paper, proving the full Promotion Gate end-to-end
11. Backtesting Engine + Walk-Forward Validation
12. Paper Trading mode against broker sandbox data
13. Reconciliation engine
14. Additional strategy sources: TradingView Webhooks (with signature/replay security), REST/WebSocket triggers, MT5 bridge, Excel/Sheets (structured rule parsing only)
15. AI Features (strategy assistant, code generation with mandatory human code review, debugging, log analysis, risk explanation, trade journal, documentation) — all advisory, all routed through the same Promotion Gate for any generated strategy code
16. Portfolio Management, Position Tracking, Holdings, Funds dashboards
17. Notification System, Scheduler, Event Bus, Plugin System
18. Additional broker adapters (each independently sandbox-validated and security-reviewed)
19. **Live Trading mode** — enabled only after Risk Engine, Reconciliation, Kill Switch, Sandbox, and Strategy Promotion Gate all have their own extensive, passing test suites; rolled out with small-capital/gradual-increase controls
20. Observability (Prometheus, Grafana, Loki, OpenTelemetry), full dashboards
21. Security hardening, load testing
22. Production deployment, deployment guide

---

## Definition of Done (Per Milestone)

- [ ] No placeholder code — especially none in OMS, Risk Engine, Strategy Execution Sandbox, or reconciliation logic
- [ ] If order placement involved: idempotency proven by test, pre-trade risk checks proven blocking by test
- [ ] If a strategy source involved: sandbox isolation and static-analysis tests passing before it can reach backtesting
- [ ] If AI-generated code involved: human code review step proven present before sandbox entry; no auto-promotion bypass
- [ ] If broker adapter involved: sandbox integration + security review passing before Live-Trading eligibility
- [ ] If webhook/external trigger involved: authentication + replay-protection tests passing
- [ ] If real-time data involved: staleness detection and fail-safe pause tested
- [ ] Kill Switch and hard-stop risk limits tested explicitly wherever relevant
- [ ] Tests written and passing, including all applicable trading/security categories; coverage target met for OMS/Risk Engine/Sandbox specifically, no exceptions
- [ ] Security review completed for this milestone's scope
- [ ] Documentation and project roadmap updated
- [ ] Commit(s) follow the planned sequence, each leaving the project in a working state
- [ ] Milestone branch pushed to remote; `CHANGELOG.md` updated; tagged on `main` after merge approval
- [ ] Explicit "why" reasoning and trade-offs given for every architectural and risk-control decision
- [ ] No strategy has skipped a Strategy Promotion Gate stage, regardless of source
- [ ] Explicit approval received before proceeding to the next commit
