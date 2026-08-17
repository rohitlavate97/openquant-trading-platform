"""Application service for system observability, Prometheus metrics aggregation, and Grafana dashboards."""

from typing import Any
from openquant.adapters.observability.prometheus_metrics import metrics
from openquant.adapters.observability.telemetry import trace_collector, SpanRecord


class ObservabilityService:
    """Provides high-level metrics snapshots, distributed trace retrieval, and Grafana dashboard templates."""

    def __init__(self) -> None:
        self._metrics = metrics
        self._trace_collector = trace_collector

    def get_raw_prometheus_metrics(self) -> str:
        """Render raw Prometheus exposition formatted text."""
        return self._metrics.generate_prometheus_text()

    def get_metrics_summary(self) -> dict[str, Any]:
        """Aggregate snapshot of system telemetry for client consoles."""
        orders_samples = self._metrics.orders_total.get_samples()
        total_orders = sum(s.value for s in orders_samples)

        risk_samples = self._metrics.risk_evaluations_total.get_samples()
        total_risk_checks = sum(s.value for s in risk_samples)

        ticks_samples = self._metrics.market_ticks_total.get_samples()
        total_ticks = sum(s.value for s in ticks_samples)

        http_samples = self._metrics.http_requests_total.get_samples()
        total_http = sum(s.value for s in http_samples)

        return {
            "total_orders_placed": int(total_orders),
            "total_risk_checks_evaluated": int(total_risk_checks),
            "total_market_ticks_ingested": int(total_ticks),
            "total_http_requests_handled": int(total_http),
            "active_spans_in_buffer": len(self._trace_collector.get_recent_spans(limit=500)),
            "kill_switch_active": any(s.value > 0 for s in self._metrics.kill_switch_status.get_samples()),
        }

    def get_recent_traces(self, limit: int = 50, trace_id: str | None = None) -> list[dict[str, Any]]:
        """Retrieve recent distributed trace spans."""
        spans = self._trace_collector.get_recent_spans(limit=limit, trace_id=trace_id)
        return [
            {
                "trace_id": s.trace_id,
                "span_id": s.span_id,
                "parent_span_id": s.parent_span_id,
                "name": s.name,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "duration_ms": round(s.duration_ms, 3),
                "attributes": s.attributes,
                "status": s.status,
                "error_message": s.error_message,
            }
            for s in spans
        ]

    def get_grafana_dashboards(self) -> list[dict[str, Any]]:
        """Return exportable Grafana dashboard definitions."""
        return [
            {
                "id": "openquant-trading-ops",
                "title": "OpenQuant - Trading Operations & OMS",
                "description": "Real-time order throughput, fill latencies, and broker adapter execution",
                "panels_count": 6,
                "tags": ["trading", "oms", "brokers"],
                "schema_version": 38,
            },
            {
                "id": "openquant-risk-controls",
                "title": "OpenQuant - Pre-Trade Risk & Kill Switch",
                "description": "Pre-trade hard stop evaluations, rate limiters, and emergency kill switch status",
                "panels_count": 5,
                "tags": ["risk", "kill-switch", "compliance"],
                "schema_version": 38,
            },
            {
                "id": "openquant-market-data",
                "title": "OpenQuant - Market Data & Feed Latency",
                "description": "3000ms staleness monitoring, tick ingestion rates, and WebSocket broadcasting",
                "panels_count": 4,
                "tags": ["market-data", "staleness", "websockets"],
                "schema_version": 38,
            },
        ]


# Global singleton service
observability_service = ObservabilityService()
