# Milestone 18: Additional Broker Adapters

## Overview
Milestone 18 expands the OpenQuant execution connectivity matrix by introducing three major institutional and retail broker adapters: **Interactive Brokers (TWS / IB Gateway)**, **Angel One SmartAPI**, and **Binance Crypto (Spot & USDT-M Perpetual Futures)**. Each adapter is decoupled from the OMS and Market Data engine via the unified `IBrokerAdapter` port and is systematically certified through the automated 5-point `BrokerAdapterCertificationHarness` (Non-Negotiable Rule 9).

## Key Deliverables & Architecture

### 1. Interactive Brokers Adapter (`src/openquant/adapters/brokers/interactive_brokers_adapter.py`)
- **Adapter ID**: `interactive_brokers`
- **Display Name**: `Interactive Brokers (TWS / IB Gateway)`
- **Asset Classes**: `EQUITY`, `FUTURE`, `OPTION`, `FOREX`, `BOND`, `COMMODITY`
- **Supported Order Types**: `MARKET`, `LIMIT`, `STOP`, `STOP_LIMIT`, `TRAILING_STOP`, `MOC`, `LOC`
- **Capabilities**:
  - Connects to TWS or IB Gateway socket/REST endpoints.
  - Multi-asset contract lookup, order placement, modification, and cancellation.
  - Position synchronization and real-time margin/equity telemetry.

### 2. Angel One SmartAPI Adapter (`src/openquant/adapters/brokers/angelone_adapter.py`)
- **Adapter ID**: `angel_one`
- **Display Name**: `Angel One SmartAPI`
- **Asset Classes**: `EQUITY`, `FUTURE`, `OPTION`, `COMMODITY`, `CURRENCY`
- **Supported Order Types**: `MARKET`, `LIMIT`, `STOPLOSS_LIMIT`, `STOPLOSS_MARKET`, `ROBO`
- **Capabilities**:
  - TOTP authentication handshake and JWT session lifecycle.
  - Real-time order execution, position tracking, and DP portfolio holdings query.
  - Instrument master token resolution and margin limits integration.

### 3. Binance Crypto Adapter (`src/openquant/adapters/brokers/binance_adapter.py`)
- **Adapter ID**: `binance_crypto`
- **Display Name**: `Binance Crypto (Spot & USDT-M Futures)`
- **Asset Classes**: `CRYPTO_SPOT`, `CRYPTO_PERPETUAL`, `CRYPTO_FUTURES`
- **Supported Order Types**: `MARKET`, `LIMIT`, `STOP_LOSS_LIMIT`, `TAKE_PROFIT_LIMIT`, `TRAILING_STOP_MARKET`
- **Capabilities**:
  - HMAC-SHA256 authenticated REST request signing and WebSocket feed.
  - USDT-M perpetual contract order routing and leverage margin calculation.
  - Spot asset balance and perpetual futures position management.

### 4. Broker Registry Integration (`src/openquant/adapters/brokers/registry.py`)
- Populated default `BrokerAdapterRegistry` with all 5 certified adapters:
  1. `paper_broker` (OpenQuant Paper Engine)
  2. `zerodha` (Zerodha Kite Connect)
  3. `interactive_brokers` (Interactive Brokers TWS / IB Gateway)
  4. `angel_one` (Angel One SmartAPI)
  5. `binance_crypto` (Binance Crypto Spot & Futures)

### 5. Automated Certification & Security Audit (Rule 9)
- All 5 adapters systematically evaluated against the 5-point harness:
  1. `CREDENTIAL_LEAKAGE_AUDIT`: Zero plaintext secrets or leaked keys.
  2. `AUTH_HANDSHAKE_VALIDATION`: Clean connection and disconnect state machine.
  3. `SANDBOX_ORDER_LIFECYCLE`: Order dispatch, execution report receipt, broker ID generation.
  4. `POSITIONS_AND_FUNDS_INTEGRITY`: Accurate margin, cash balance, and portfolio valuations.
  5. `FAULT_TOLERANCE_AND_SHUTDOWN`: Graceful failure handling and reconnect capability.

### 6. Frontend Broker Adapters Page (`frontend/src/features/brokers/BrokerAdaptersPage.tsx`)
- Card grid rendering all 5 registered broker adapters with asset classes, order types, and live eligibility badges.
- Dynamic funds and margin display formatted by broker currency (`$`, `₹`, `₮`).
- 1-Click "Audit Harness" button triggering live certification audit per adapter.

## Test Verification
- **Backend**: **141 Unit & Integration tests passing** (84% coverage).
- **Frontend**: **37 Vitest tests passing** across 17 test files, 0 TypeScript errors, clean production bundle.
