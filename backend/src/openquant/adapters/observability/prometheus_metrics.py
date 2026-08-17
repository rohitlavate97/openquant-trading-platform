"""High-performance thread-safe Prometheus Metrics Collector and OpenMetrics exporter."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
import threading
from typing import Any


@dataclass
class MetricSample:
    name: str
    labels: dict[str, str]
    value: float
    timestamp: float | None = None


class Counter:
    """Thread-safe Prometheus Counter metric."""

    def __init__(self, name: str, documentation: str, labelnames: list[str]) -> None:
        self.name = name
        self.doc = documentation
        self.labelnames = labelnames
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def _labels_key(self, labels: dict[str, str]) -> tuple[tuple[str, str], ...]:
        return tuple(sorted((k, str(labels.get(k, ""))) for k in self.labelnames))

    def inc(self, amount: float = 1.0, **labels: Any) -> None:
        key = self._labels_key({k: str(v) for k, v in labels.items()})
        with self._lock:
            self._values[key] += amount

    def get_samples(self) -> list[MetricSample]:
        with self._lock:
            return [
                MetricSample(name=self.name, labels=dict(k), value=v)
                for k, v in self._values.items()
            ]


class Gauge:
    """Thread-safe Prometheus Gauge metric."""

    def __init__(self, name: str, documentation: str, labelnames: list[str]) -> None:
        self.name = name
        self.doc = documentation
        self.labelnames = labelnames
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def _labels_key(self, labels: dict[str, str]) -> tuple[tuple[str, str], ...]:
        return tuple(sorted((k, str(labels.get(k, ""))) for k in self.labelnames))

    def set(self, value: float, **labels: Any) -> None:
        key = self._labels_key({k: str(v) for k, v in labels.items()})
        with self._lock:
            self._values[key] = value

    def inc(self, amount: float = 1.0, **labels: Any) -> None:
        key = self._labels_key({k: str(v) for k, v in labels.items()})
        with self._lock:
            self._values[key] += amount

    def dec(self, amount: float = 1.0, **labels: Any) -> None:
        key = self._labels_key({k: str(v) for k, v in labels.items()})
        with self._lock:
            self._values[key] -= amount

    def get_samples(self) -> list[MetricSample]:
        with self._lock:
            return [
                MetricSample(name=self.name, labels=dict(k), value=v)
                for k, v in self._values.items()
            ]


class Histogram:
    """Thread-safe Prometheus Histogram metric with configurable duration/size buckets."""

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: list[str],
        buckets: tuple[float, ...] = DEFAULT_BUCKETS,
    ) -> None:
        self.name = name
        self.doc = documentation
        self.labelnames = labelnames
        self.buckets = tuple(sorted(buckets))
        self._counts: dict[tuple[tuple[str, str], ...], int] = defaultdict(int)
        self._sums: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._bucket_counts: dict[tuple[tuple[str, str], ...], dict[float, int]] = defaultdict(
            lambda: {b: 0 for b in self.buckets}
        )
        self._lock = threading.Lock()

    def _labels_key(self, labels: dict[str, str]) -> tuple[tuple[str, str], ...]:
        return tuple(sorted((k, str(labels.get(k, ""))) for k in self.labelnames))

    def observe(self, amount: float, **labels: Any) -> None:
        key = self._labels_key({k: str(v) for k, v in labels.items()})
        with self._lock:
            self._counts[key] += 1
            self._sums[key] += amount
            bucket_dict = self._bucket_counts[key]
            for b in self.buckets:
                if amount <= b:
                    bucket_dict[b] += 1

    def get_samples(self) -> list[MetricSample]:
        samples: list[MetricSample] = []
        with self._lock:
            for key, count in self._counts.items():
                lbls = dict(key)
                # Buckets
                b_dict = self._bucket_counts[key]
                for b in self.buckets:
                    b_lbls = {**lbls, "le": str(b)}
                    samples.append(MetricSample(name=f"{self.name}_bucket", labels=b_lbls, value=float(b_dict[b])))
                # +Inf bucket
                samples.append(MetricSample(name=f"{self.name}_bucket", labels={**lbls, "le": "+Inf"}, value=float(count)))
                # Count and Sum
                samples.append(MetricSample(name=f"{self.name}_count", labels=lbls, value=float(count)))
                samples.append(MetricSample(name=f"{self.name}_sum", labels=lbls, value=float(self._sums[key])))
        return samples


class MetricsRegistry:
    """Central Prometheus Metrics Registry for OpenQuant."""

    def __init__(self) -> None:
        # Trading Operations & OMS
        self.orders_total = Counter(
            name="openquant_orders_total",
            documentation="Total orders placed by status, broker, and symbol",
            labelnames=["status", "broker_id", "symbol"],
        )
        self.order_latency_seconds = Histogram(
            name="openquant_order_latency_seconds",
            documentation="Order execution latency in seconds",
            labelnames=["operation", "broker_id"],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
        )

        # Risk Engine & Kill Switch
        self.risk_evaluations_total = Counter(
            name="openquant_risk_evaluations_total",
            documentation="Total pre-trade risk checks evaluated by verdict and rule",
            labelnames=["verdict", "rule"],
        )
        self.risk_evaluation_duration_seconds = Histogram(
            name="openquant_risk_evaluation_duration_seconds",
            documentation="Duration of synchronous pre-trade risk engine hard-stop evaluation",
            labelnames=["stage"],
            buckets=(0.0001, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.025),
        )
        self.kill_switch_status = Gauge(
            name="openquant_kill_switch_active",
            documentation="State of the Global Emergency Kill Switch (1=Active, 0=Unlocked)",
            labelnames=["level"],
        )

        # Market Data Staleness & Feed Health (Rule 7)
        self.market_ticks_total = Counter(
            name="openquant_market_ticks_total",
            documentation="Total ingested market data ticks by symbol and feed source",
            labelnames=["symbol", "source"],
        )
        self.market_staleness_ms = Gauge(
            name="openquant_market_data_staleness_ms",
            documentation="Latest market tick age in milliseconds per symbol",
            labelnames=["symbol"],
        )

        # State Reconciliation Drift (Rule 5)
        self.reconciliation_discrepancies = Gauge(
            name="openquant_reconciliation_discrepancy_count",
            documentation="Active position/fill mismatches detected between OMS and Broker actuals",
            labelnames=["account_id", "broker_id"],
        )

        # Live Strategies & System Telemetry
        self.live_sessions_active = Gauge(
            name="openquant_live_sessions_active",
            documentation="Number of active Stage 4 Live Trading Strategy Sessions",
            labelnames=["broker_id"],
        )
        self.http_requests_total = Counter(
            name="openquant_http_requests_total",
            documentation="Total incoming HTTP REST API requests by method, endpoint, and status",
            labelnames=["method", "endpoint", "status_code"],
        )
        self.http_request_duration_seconds = Histogram(
            name="openquant_http_request_duration_seconds",
            documentation="HTTP REST API request duration in seconds",
            labelnames=["method", "endpoint"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
        )

    def generate_prometheus_text(self) -> str:
        """Render all registered metrics in standard Prometheus exposition format."""
        lines: list[str] = []

        metrics_list = [
            (self.orders_total, "counter"),
            (self.order_latency_seconds, "histogram"),
            (self.risk_evaluations_total, "counter"),
            (self.risk_evaluation_duration_seconds, "histogram"),
            (self.kill_switch_status, "gauge"),
            (self.market_ticks_total, "counter"),
            (self.market_staleness_ms, "gauge"),
            (self.reconciliation_discrepancies, "gauge"),
            (self.live_sessions_active, "gauge"),
            (self.http_requests_total, "counter"),
            (self.http_request_duration_seconds, "histogram"),
        ]

        for metric, mtype in metrics_list:
            lines.append(f"# HELP {metric.name} {metric.doc}")
            lines.append(f"# TYPE {metric.name} {mtype}")
            samples = metric.get_samples()
            if not samples:
                # Default zero sample if no observations yet
                if mtype == "gauge":
                    lines.append(f"{metric.name} 0")
            for sample in samples:
                if sample.labels:
                    lbl_str = ",".join(f'{k}="{v}"' for k, v in sample.labels.items())
                    lines.append(f"{sample.name}{{{lbl_str}}} {sample.value}")
                else:
                    lines.append(f"{sample.name} {sample.value}")

        return "\n".join(lines) + "\n"


# Global singleton registry
metrics = MetricsRegistry()
