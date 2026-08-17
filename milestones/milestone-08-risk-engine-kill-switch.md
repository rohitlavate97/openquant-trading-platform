# Milestone 08: Risk Engine & Global Kill Switch

**Status:** Completed  
**Branch:** `milestone-08-risk-engine-kill-switch`  
**PR:** [milestone-08-risk-engine-kill-switch](https://github.com/rohitlavate97/openquant-trading-platform/pull/new/milestone-08-risk-engine-kill-switch)  
**Date:** 2026-08-17  

---

## 1. Objectives & Architectural Decisions

- **Synchronous Pre-Trade Risk Engine (Non-Negotiable Rule 2 & 4)**:
  - Synchronously evaluates **every** order request before routing to any broker adapter.
  - Hard stops strictly enforced with **zero async bypass**:
    1. **Kill Switch Guard**: Verifies global, account, strategy, and symbol kill switch flags.
    2. **Daily Loss Limit**: Blocks trading when session loss breaches configured threshold (default 3.0% of equity).
    3. **Peak Drawdown Limit**: Blocks trading when high watermark drawdown breaches limit (default 5.0%).
    4. **Order Rate Limiter**: Enforces high-frequency order caps within a sliding 1-second window (default 10 orders/sec).
    5. **Position Sizing & Notional Cap**: Ensures single order value does not exceed maximum equity percentage (default 10.0%).
    6. **Self-Trade Prevention**: Disallows crossing limit orders on resting opposite-side orders for the same account and symbol.
    7. **Open Orders per Symbol Cap**: Limits open active orders per instrument (default 10).
    8. **Pre-Trade Staleness**: Integrated with 3000ms market data freshness assertion (Rule 7).
- **1-Click Emergency Kill Switch**:
  - Global, Account-level, Strategy-level, and Symbol-level emergency shutdown.
  - Automatically cancels all open broker orders across accounts.
  - Optional market flattening of all open active positions.
  - Emits real-time `KILL_SWITCH_STATUS_CHANGED` telemetry over WebSockets and records high-severity compliance logs in `IAuditLogRepository`.
- **Risk REST Endpoints (`/api/v1/risk/*`)**:
  - `GET /api/v1/risk/config`: Inspect active risk limits and kill switch state.
  - `PUT /api/v1/risk/config`: Update risk limits (Admin restricted).
  - `POST /api/v1/risk/kill-switch/activate`: 1-Click emergency kill switch trigger with scope and optional position flattening.
  - `POST /api/v1/risk/kill-switch/deactivate`: Reset kill switch and resume trading.
  - `POST /api/v1/risk/evaluate-pre-trade`: Dry-run pre-trade risk evaluation without placing orders.
- **Frontend Risk Management UI (`RiskManagementPage.tsx`)**:
  - Emergency Kill Switch banner and modal with level selectors (GLOBAL, ACCOUNT, STRATEGY, SYMBOL) and position flattening checkbox.
  - Pre-Trade Hard-Stop Parameters configuration panel with interactive range sliders and live feedback.
  - Pre-Trade Risk Engine Dry-Run Simulator: tests any order against all 8 checks with individual pass/fail badges.
  - Top header kill switch directly connected to live API endpoints.

---

## 2. Deliverables & Files Created

- **Backend**:
  - `src/openquant/domain/models/risk.py` (`RiskLimitsConfig`, `KillSwitchState`, `KillSwitchLevel`, `RiskCheckType`)
  - `src/openquant/adapters/risk/risk_engine.py` (`SynchronousRiskEngine`)
  - `src/openquant/application/services/risk_service.py` (`RiskService`)
  - `src/openquant/interfaces/api/v1/endpoints/risk.py`
- **Frontend**:
  - `src/types/risk.ts`
  - `src/features/risk/RiskManagementPage.tsx`
  - `src/features/risk/RiskManagementPage.test.tsx`
  - `src/App.tsx`
- **Tests**:
  - `backend/tests/unit/application/test_risk_service.py`
  - `backend/tests/integration/test_risk_api.py`

---

## 3. Test & Verification Results

- **Backend Pytest Suite**: **66 passed in 11.70s** (83% coverage, 100% on domain layer)
- **Hexagonal Boundary Test**: **Passed** (Zero infrastructure leaks)
- **Frontend Vitest Suite**: **16 passed**
- **Frontend Type Check (`tsc --noEmit`)**: **0 errors**
- **Frontend Production Bundle Build**: **Success (`dist/` built in 4.17s)**
