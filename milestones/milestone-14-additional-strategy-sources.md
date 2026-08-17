# Milestone 14: Additional Strategy Sources

**Status:** Completed  
**Branch:** `milestone-14-additional-strategy-sources`  
**PR:** [milestone-14-additional-strategy-sources](https://github.com/rohitlavate97/openquant-trading-platform/pull/new/milestone-14-additional-strategy-sources)  
**Date:** 2026-08-17  

---

## 1. Objectives & Architectural Decisions

- **Signed TradingView Webhook Ingestion ([`tradingview_webhook.py`](file:///D:/Projects/AI/openquant-trading-platform/backend/src/openquant/adapters/sources/tradingview_webhook.py))**:
  - Implements `ITradingViewWebhookHandler` domain port.
  - Verifies cryptographic HMAC-SHA256 signatures (`hmac.new(secret, msg, sha256).hexdigest()`) from alert payloads or `X-TradingView-Signature` HTTP headers.
  - Replay attack & clock skew defense with dynamic memory sliding nonce cache and strict $\le 60\text{s}$ TTL.
  - Translates verified alerts into `OrderRequest` and routes synchronously into pre-trade risk evaluation (Rules 2, 4, 7, 8) before OMS execution.
- **MetaTrader 5 (MT5) ZeroMQ Bridge ([`mt5_bridge.py`](file:///D:/Projects/AI/openquant-trading-platform/backend/src/openquant/adapters/sources/mt5_bridge.py))**:
  - Implements `IMT5BridgeAdapter` domain port for low-latency IPC socket communication with MT5 Expert Advisors (EAs).
  - Handles bidirectional wire commands (`MT5BridgeCommand`), inbound heartbeat monitoring with stale disconnection timeout, and execution confirmation telemetry.
- **Structured Google Sheets / CSV Parser ([`sheets_parser.py`](file:///D:/Projects/AI/openquant-trading-platform/backend/src/openquant/adapters/sources/sheets_parser.py))**:
  - Implements `IStructuredSheetsParser` domain port.
  - Validates tabular strategy signals against strict schema constraints: `Timestamp`, `Symbol`, `Signal_Type` (`BUY`/`SELL`/`CLOSE`), `Quantity` ($> 0$), `Limit_Price`, `Stop_Loss`, `Take_Profit`, `Strategy_Tag`.
  - Rejects malformed rows with granular validation diagnostics while enabling 1-click batch execution of valid orders through OMS.
- **Strategy Sources Application Service ([`strategy_sources_service.py`](file:///D:/Projects/AI/openquant-trading-platform/backend/src/openquant/application/services/strategy_sources_service.py))**:
  - Coordinates webhook processing, MT5 EA socket command dispatch, and CSV batch order submission with immutable compliance audit logs (`IAuditLogRepository`).
- **Strategy Sources REST API ([`strategy_sources.py`](file:///D:/Projects/AI/openquant-trading-platform/backend/src/openquant/interfaces/api/v1/endpoints/strategy_sources.py))**:
  - `POST /api/v1/sources/tradingview/webhook`: Public webhook endpoint with HMAC validation & replay protection.
  - `GET /api/v1/sources/mt5/status`: Real-time MT5 bridge telemetry.
  - `POST /api/v1/sources/mt5/command`: Outbound command dispatch to MT5 EA.
  - `POST /api/v1/sources/sheets/parse`: Ingest & validate raw CSV/Google Sheet rows.
  - `POST /api/v1/sources/sheets/execute`: Batch order submission via OMS.
- **Frontend Strategy Sources UI ([`StrategySourcesPage.tsx`](file:///D:/Projects/AI/openquant-trading-platform/frontend/src/features/sources/StrategySourcesPage.tsx))**:
  - TradingView Webhook Generator & Live Dispatch Tester with JSON payload generator and instant receipt modal.
  - MT5 ZeroMQ Bridge Telemetry card with live EA status, roundtrip latency, and manual trade dispatcher.
  - Structured Sheets / CSV Ingestion tool with row validation table and batch execution trigger.

---

## 2. Deliverables & Files Created

- **Backend**:
  - `src/openquant/domain/models/strategy_sources.py`
  - `src/openquant/domain/ports/strategy_sources_port.py`
  - `src/openquant/adapters/sources/tradingview_webhook.py`
  - `src/openquant/adapters/sources/mt5_bridge.py`
  - `src/openquant/adapters/sources/sheets_parser.py`
  - `src/openquant/application/services/strategy_sources_service.py`
  - `src/openquant/interfaces/api/v1/endpoints/strategy_sources.py`
- **Frontend**:
  - `src/types/sources.ts`
  - `src/features/sources/StrategySourcesPage.tsx`
  - `src/features/sources/StrategySourcesPage.test.tsx`
  - `src/components/layout/Sidebar.tsx`
  - `src/App.tsx`
- **Tests**:
  - `backend/tests/unit/domain/test_strategy_sources_models.py`
  - `backend/tests/unit/adapters/test_tradingview_webhook.py`
  - `backend/tests/unit/adapters/test_mt5_bridge.py`
  - `backend/tests/unit/adapters/test_sheets_parser.py`
  - `backend/tests/unit/application/test_strategy_sources_service.py`
  - `backend/tests/integration/test_strategy_sources_api.py`

---

## 3. Test & Verification Results

- **Backend Pytest Suite**: **118 passed in 17.47s** (85% code coverage)
- **Hexagonal Boundary Test**: **Passed** (0 unauthorized imports in domain)
- **Frontend Vitest Suite**: **30 passed in 5.14s**
- **Frontend Type Check (`tsc --noEmit`)**: **0 errors**
- **Frontend Production Bundle Build**: **Success (`dist/` built in 3.03s)**
