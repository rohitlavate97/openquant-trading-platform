# Milestone 20: Observability & Monitoring

## Overview
Milestone 20 introduces enterprise-grade **Observability, Distributed Tracing, Prometheus Telemetry, and Grafana Integration** to the OpenQuant platform. The platform now natively measures order throughput, synchronous pre-trade risk evaluation latencies, market data tick staleness against the 3000ms threshold (Rule 7), position reconciliation drift (Rule 5), and distributed request lifecycles tagged with `X-Correlation-ID` context propagation across all HTTP and WebSocket endpoints.

---

## Key Deliverables & Architecture

### 1. High-Performance Prometheus Metrics Engine (`openquant.adapters.observability.prometheus_metrics`)
- **Metric Types**: Thread-safe implementations of `Counter`, `Gauge`, and `Histogram` with customizable latency buckets.
- **Key OpenQuant Metric Expositions**:
  - `openquant_orders_total{status, broker_id, symbol}`: Total order lifecycle counts.
  - `openquant_order_latency_seconds{operation, broker_id}`: High-precision order routing and execution duration.
  - `openquant_risk_evaluations_total{verdict, rule}`: Pre-trade hard stop evaluations and rejections.
  - `openquant_risk_evaluation_duration_seconds{stage}`: Synchronous pre-trade risk check latency.
  - `openquant_kill_switch_active{level}`: Global emergency kill switch status gauge.
  - `openquant_market_ticks_total{symbol, source}`: Tick ingestion volume per instrument.
  - `openquant_market_data_staleness_ms{symbol}`: Latency and staleness age per symbol.
  - `openquant_reconciliation_discrepancy_count{account_id, broker_id}`: Active position mismatches.
  - `openquant_live_sessions_active{broker_id}`: Active Stage 4 live trading sessions.
  - `openquant_http_requests_total{method, endpoint, status_code}`: HTTP traffic metrics.
  - `openquant_http_request_duration_seconds{method, endpoint}`: HTTP latency distribution.
- **Exposition Format**: Standard Prometheus text format (version 0.0.4) served directly at `/metrics`.

### 2. OpenTelemetry Tracing & Correlation Context (`openquant.adapters.observability.telemetry`)
- `correlation_id_ctx`: ContextVar tracking execution correlation IDs across asynchronous coroutine boundaries.
- `CorrelationIdMiddleware`: FastAPI middleware automatically extracting or provisioning `X-Correlation-ID` header and tracking HTTP request latency into Prometheus histograms.
- `trace_span(name, attributes)`: OpenTelemetry-compatible context manager recording trace spans, duration, status, and capturing error messages.
- `InMemoryTraceCollector`: Circular buffer of distributed trace spans queryable by trace ID or operation name.

### 3. Observability Application Service & REST API
- `ObservabilityService` (`openquant.application.services.observability_service.py`):
  - Aggregates telemetry summaries, recent trace spans, and Grafana dashboard templates.
- **Endpoints**:
  - `GET /metrics`: Prometheus scraping endpoint (`text/plain; version=0.0.4`).
  - `GET /api/v1/observability/summary`: High-level system telemetry JSON.
  - `GET /api/v1/observability/traces`: Query recent distributed trace spans and timings.
  - `GET /api/v1/observability/dashboards`: Pre-configured Grafana dashboard templates.

### 4. Grafana Dashboards Suite (`deployments/grafana/dashboards/`)
- `trading-operations.json`: Rate of orders placed by status, p95 and p99 fill latency panels.
- `risk-controls.json`: Kill Switch status indicator, pre-trade hard stop evaluations & breach rates.
- `market-data-latency.json`: 3000ms staleness threshold time series, tick ingestion volume by feed.

### 5. Frontend Observability Console (`ObservabilityPage.tsx`)
- **Telemetry Overview**: Real-time counters for HTTP requests, synchronous risk evaluations, market data ticks, and active trace spans.
- **Distributed Traces Explorer**: Interactive table of recent spans with duration in ms, status tags, and correlation ID search.
- **Prometheus Exporter Live View**: In-browser preview and 1-click copy for the `/metrics` endpoint.
- **Grafana Dashboards Gallery**: 1-click exportable JSON templates for Grafana 10+ deployment.

---

## Verification & Test Results

- **Backend Pytest Suite**: **156 passed in 32.02s** (85% total code coverage).
  - Unit tests: `test_prometheus_metrics.py`, `test_telemetry.py`.
  - Integration tests: `test_observability_api.py`.
- **Frontend Vitest Suite**: **19 test files, 42 passed in 12.15s**.
  - Component tests: `ObservabilityPage.test.tsx`.
- **Production Build**: TypeScript typecheck passed; Vite production build bundled cleanly in 7.16s.
