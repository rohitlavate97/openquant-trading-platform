# Milestone 19: Live Trading Mode

## Overview
Milestone 19 introduces the **Production Live Trading Engine & Launch Control System** to OpenQuant. Live Trading Mode allows quant strategies that have successfully graduated through the 7-stage promotion lifecycle (Stage 4: LIVE_TRADING) to be activated against connected broker adapters (Interactive Brokers, Binance Crypto, Zerodha Kite, Angel One SmartAPI, Paper Sandbox) under strict non-negotiable safety rules, automated 5-point preflight verification, gradual position scaling (Starter 25% → Intermediate 50% → Full 100%), dual-operator authorization, and 1-click emergency halt mechanisms.

---

## Key Deliverables & Architecture

### 1. Domain Models (`openquant.domain.models.live_trading`)
- `LiveTradingState`: `READY` | `PREFLIGHT_CHECKING` | `ACTIVE` | `HALTED` | `TERMINATED`.
- `ScalingTier`:
  - `TIER_1_STARTER`: 25% capital multiplier for initial execution and slippage calibration.
  - `TIER_2_INTERMEDIATE`: 50% capital multiplier after initial consistency validation.
  - `TIER_3_FULL`: 100% full authorized capital allocation.
- `LiveCapitalAllocation`: Sizing parameters enforcing `total_authorized_capital`, `scaling_tier`, `max_order_notional`, `margin_floor_buffer`, `max_daily_loss`, and `max_drawdown_percent`.
- `LivePreflightCheckItem` & `LivePreflightReport`: Automated 5-point readiness matrix.
- `LiveStrategySession`: Active live strategy execution telemetry, realized/unrealized PnL, filled orders count, scaling state, dual approver verification, and halt reason tracking.

### 2. Domain Ports (`openquant.domain.ports.live_trading_port`)
- `ILiveSessionRepository`: Abstract repository interface for live session persistence.
- `ILiveTradingService`: Service interface defining `run_preflight_check`, `activate_live_session`, `adjust_scaling_tier`, `halt_live_session`, `get_session`, and `list_sessions`.

### 3. Automated 5-Point Preflight Verification Matrix (Non-Negotiable Guardrails)
1. **Rule 1 - Stage 4 Promotion Gate Verification**: Verifies strategy stage is strictly `StrategyPromotionStage.LIVE_TRADING`.
2. **Rule 9 - Certified Broker Adapter Audit**: Verifies broker adapter has `is_certified == True` and passed the 5-point automated sandbox certification harness.
3. **Rules 2 & 4 - Pre-Trade Risk Engine Status**: Verifies Pre-Trade Risk Engine is active and Global Emergency Kill Switch is unlocked.
4. **Rule 7 - Market Data Staleness Engine (< 3000ms)**: Verifies feed latency for all instruments does not exceed 3000ms staleness threshold.
5. **Broker Authenticated Session Handshake**: Verifies active authenticated session with target broker.

### 4. Application Service (`LiveTradingService`)
- Coordinates preflight validation across `StrategyService`, `BrokerAdapterRegistry`, `RiskService`, and `MarketDataService`.
- Enforces single active live session constraint per strategy.
- Enforces dual-operator confirmation for production order routing.
- Emits domain events (`live_trading.activated`, `live_trading.scaled`, `live_trading.halted`) over `IEventBus`.
- Records immutable audit trail records (`LIVE_SESSION_ACTIVATED`, `LIVE_SESSION_SCALED`, `LIVE_SESSION_HALTED`) in `AuditLogService`.

### 5. REST API Endpoints (`/api/v1/live-trading`)
- `POST /api/v1/live-trading/preflight`: Evaluates 5-point preflight readiness checklist.
- `POST /api/v1/live-trading/sessions`: Activates live session with capital allocation and dual approver verification.
- `GET /api/v1/live-trading/sessions`: Lists active and historical live sessions.
- `GET /api/v1/live-trading/sessions/{session_id}`: Retrieves live session details and telemetry.
- `POST /api/v1/live-trading/sessions/{session_id}/scale`: Adjusts scaling tier (Starter 25%, Intermediate 50%, Full 100%).
- `POST /api/v1/live-trading/sessions/{session_id}/halt`: Triggers manual or automated emergency session halt.

### 6. Frontend Live Trading Mission Control (`LiveTradingConsolePage.tsx`)
- **Mission Control Header**: Live status indicator, active session counter, total live allocated capital ticker.
- **Launch Pad Card**: Strategy selector, broker selector, capital allocation calculator, scaling tier selector, and effective capital banner.
- **Interactive Preflight Verification Matrix**: Real-time pass/fail badges across all 5 non-negotiable checks.
- **Dual Confirmation Verification Modal**: Mandatory secondary approver ID confirmation.
- **Active Live Strategies Dashboard**: Live session telemetry cards with real-time PnL, filled orders count, 1-click tier scaling, and red **Emergency Halt** button.

---

## Verification & Test Results

- **Backend Pytest Suite**: **147 passed in 29.16s** (85% total code coverage).
  - Unit tests: `test_live_trading_models.py`, `test_live_trading_service.py`.
  - Integration tests: `test_live_trading_api.py`.
- **Frontend Vitest Suite**: **18 test files, 40 passed in 13.81s**.
  - Component tests: `LiveTradingConsolePage.test.tsx`.
- **Production Bundle**: TypeScript typecheck passed; Vite production build generated in 5.53s.
