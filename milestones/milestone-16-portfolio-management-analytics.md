# Milestone 16: Portfolio Management & Analytics

## Overview
Milestone 16 delivers real-time portfolio management, multi-account mark-to-market position tracking, dynamic asset allocation analysis, and continuous risk-adjusted performance curve monitoring in OpenQuant. It enables quant traders and risk managers to evaluate active exposure across instruments, track live unrealized/realized PnL, maintain concentration risk guardrails, and execute atomic 1-click position flattening directly through the Order Management System (OMS).

## Key Deliverables & Architecture

### 1. Domain Models (`src/openquant/domain/models/portfolio.py`)
- **`PortfolioPosition`**: Mark-to-market valued position with current mark price, cost basis, unrealized PnL, unrealized PnL %, and total portfolio weight %.
- **`AssetAllocationItem`**: Percentage and nominal market value breakdown by instrument symbol or cash buffer (`USD_CASH`).
- **`PortfolioPerformanceSnapshot`**: Historical timestamped equity curve snapshot with drawdown % and daily return %.
- **`PortfolioSummary`**: Real-time aggregated account state including total NAV, cash balance, margin used/available, peak equity watermark, current drawdown % (Rule 2 guardrail), win rate %, profit factor, and Sharpe ratio.

### 2. Domain Port & Adapters (`src/openquant/domain/ports/portfolio_port.py`, `src/openquant/adapters/portfolio/portfolio_analytics_engine.py`)
- **`IPortfolioAnalyticsEngine`**: Formal port for multi-account portfolio valuation, position aggregation, asset allocation breakdown, and historical equity curve generation.
- **`PortfolioAnalyticsEngine`**:
  - Live Mark-to-Market pricing computed against `MarketDataService` ticker feeds.
  - Multi-asset exposure weighting and concentration metrics.
  - Peak watermark equity tracking and real-time drawdown computation.

### 3. Application & API Services (`src/openquant/application/services/portfolio_service.py`, `src/openquant/interfaces/api/v1/endpoints/portfolio.py`)
- **`PortfolioService`**: Application service orchestrating analytics retrieval, multi-account aggregation, and position closing via OMS with audit log emission.
- **REST Endpoints**:
  - `GET /api/v1/portfolio/summary`: Account-level NAV, cash balance, margin utilization, and risk stats.
  - `GET /api/v1/portfolio/positions`: Active positions with mark price, unrealized PnL, and allocation weight.
  - `GET /api/v1/portfolio/allocation`: Asset allocation and concentration breakdown.
  - `GET /api/v1/portfolio/performance`: Equity curve and drawdown historical series.
  - `POST /api/v1/portfolio/positions/{symbol}/close`: Flatten active position via opposing market order through OMS.

### 4. Frontend Portfolio Management UI (`frontend/src/features/portfolio/PortfolioManagementPage.tsx`)
- **Top Metric Cards**: Real-time Total Equity (NAV), Unrealized/Daily PnL, Peak Drawdown % (Rule 2), and Sharpe Ratio.
- **Active Positions Table**: Detailed position matrix with 1-click Close action.
- **Asset Allocation & Concentration Risk**: Visual allocation bars with 30% concentration limit indicators.
- **Equity Curve & Drawdown Visualizer**: Historical performance series and peak-to-trough drawdown depth.

## Test Verification
- **Backend**: 130 Unit and Integration tests passing (86% coverage).
- **Frontend**: 35 Vitest tests passing across 16 test files, 0 TypeScript errors, clean production bundle.
