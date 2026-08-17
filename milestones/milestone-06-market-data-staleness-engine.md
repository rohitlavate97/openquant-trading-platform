# Milestone 06: Market Data Ingestion & Staleness Engine

**Status:** Completed  
**Branch:** `milestone-06-market-data-staleness-engine`  
**PR:** [milestone-06-market-data-staleness-engine](https://github.com/rohitlavate97/openquant-trading-platform/pull/new/milestone-06-market-data-staleness-engine)  
**Date:** 2026-08-17  

---

## 1. Objectives & Architectural Decisions

- **Pre-Trade Staleness Hard-Stop (Rule 7)**:
  - Synchronously blocks order execution if the market data tick for the instrument exceeds 3000ms.
  - Generates `StaleMarketDataError` and emits `MARKET_DATA_STALE_ALERT` telemetry to immediately pause active automated trading strategies.
- **In-Memory Feed & Staleness Engine (`InMemoryMarketDataFeed`)**:
  - High-performance, thread-safe market data cache tracking tick arrival timestamps, latency (ms), tick throughput frequency (ticks/s), and instrument health status (`HEALTHY`, `DEGRADED`, `STALE`, `DISCONNECTED`).
- **Streaming Multi-Timeframe OHLCV Bar Aggregator (`StreamingCandleAggregator`)**:
  - Aggregates streaming ticks into standard timeframe bars (`1m`, `5m`, `15m`, `1h`, `4h`, `1d`).
  - Automatically finalizes previous bars upon timeframe boundary crossing, stores historical bar sequences, and broadcasts `CANDLE_CLOSED` events over WebSockets.
- **Synthetic Market Replay & Brownian Random Walk Feed (`SyntheticMarketFeed`)**:
  - Realistic multi-asset geometric Brownian random walk simulator with realistic bid/ask spread modeling, configurable interval speed (0.2s to 1.0s), and start/stop controls for offline development and backtesting.
- **Market Data REST Endpoints (`/api/v1/market-data/`)**:
  - `GET /api/v1/market-data/ticks/latest`: Fetch latest L1 tick for all or specified symbol.
  - `GET /api/v1/market-data/candles`: Retrieve OHLCV candle bars.
  - `GET /api/v1/market-data/staleness`: System-wide feed health & staleness inspection report.
  - `POST /api/v1/market-data/ticks`: Ingest external market ticks.
  - `POST /api/v1/market-data/replay/start` & `stop`: Start/Stop synthetic market replay.
- **Frontend Market Data & Feed Health UI (`MarketDataManagementPage.tsx`)**:
  - Real-time feed health overview cards.
  - Per-symbol staleness inspector table showing tick age, frequency, and order execution status.
  - Interactive synthetic replay generator controls (speed selectors, start/stop).
  - Aggregated OHLCV candle bar visualizer with BULL/BEAR indicators.

---

## 2. Deliverables & Files Created

- **Backend**:
  - `src/openquant/domain/models/market_data.py` (enhanced with `FeedHealthStatus`, `SymbolFeedMetrics`, `MarketDataStalenessReport`)
  - `src/openquant/domain/ports/market_data_port.py` (`IMarketDataPort`, `ICandleAggregatorPort`)
  - `src/openquant/adapters/market_data/in_memory_feed.py`
  - `src/openquant/adapters/market_data/candle_aggregator.py`
  - `src/openquant/adapters/market_data/synthetic_feed.py`
  - `src/openquant/application/services/market_data_service.py`
  - `src/openquant/interfaces/api/v1/endpoints/market_data.py`
- **Frontend**:
  - `src/types/market-data.ts`
  - `src/features/market-data/MarketDataManagementPage.tsx`
  - `src/features/market-data/MarketDataManagementPage.test.tsx`
  - `src/components/layout/Sidebar.tsx`
  - `src/App.tsx`
- **Tests**:
  - `backend/tests/unit/adapters/test_market_data_adapters.py`
  - `backend/tests/unit/application/test_market_data_service.py`
  - `backend/tests/integration/test_market_data_api.py`

---

## 3. Test & Verification Results

- **Backend Pytest Suite**: **58 passed in 9.10s** (83% overall coverage, 100% on domain models)
- **Hexagonal Boundary Test**: **Passed** (0 unauthorized imports)
- **Frontend Vitest Suite**: **12 passed**
- **Frontend Type Check (`tsc --noEmit`)**: **0 errors**
- **Frontend Production Bundle Build**: **Success (`dist/` built in 13.06s)**
