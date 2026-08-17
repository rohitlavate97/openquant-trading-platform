"""OpenTelemetry-compatible Distributed Tracing, Span Collector, and Correlation Context."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
from typing import Any
import uuid
import threading
from contextlib import contextmanager

# Async context variable for Request & Execution Correlation ID
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id_ctx", default="")


def get_correlation_id() -> str:
    """Get active correlation ID from context or generate new fallback."""
    cid = correlation_id_ctx.get()
    if not cid:
        cid = f"cid_{uuid.uuid4().hex[:12]}"
        correlation_id_ctx.set(cid)
    return cid


def set_correlation_id(cid: str) -> None:
    """Set active correlation ID in context."""
    correlation_id_ctx.set(cid)


@dataclass
class SpanRecord:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "OK"
    error_message: str | None = None


class InMemoryTraceCollector:
    """Thread-safe circular trace buffer for distributed span collection and telemetry analysis."""

    def __init__(self, max_spans: int = 500) -> None:
        self._max_spans = max_spans
        self._spans: list[SpanRecord] = []
        self._lock = threading.Lock()

    def record_span(self, span: SpanRecord) -> None:
        with self._lock:
            self._spans.append(span)
            if len(self._spans) > self._max_spans:
                self._spans.pop(0)

    def get_recent_spans(self, limit: int = 50, trace_id: str | None = None) -> list[SpanRecord]:
        with self._lock:
            if trace_id:
                filtered = [s for s in self._spans if s.trace_id == trace_id]
                return list(reversed(filtered))[:limit]
            return list(reversed(self._spans))[:limit]

    def clear(self) -> None:
        with self._lock:
            self._spans.clear()


trace_collector = InMemoryTraceCollector()


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None, parent_span_id: str | None = None):
    """Context manager for tracing operations with OpenTelemetry-compatible span semantics."""
    trace_id = get_correlation_id()
    span_id = f"span_{uuid.uuid4().hex[:8]}"
    start_dt = datetime.now(timezone.utc)
    start_perf = time.perf_counter()

    span = SpanRecord(
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        name=name,
        start_time=start_dt,
        attributes=attributes or {},
    )

    try:
        yield span
        span.status = "OK"
    except Exception as exc:
        span.status = "ERROR"
        span.error_message = str(exc)
        raise
    finally:
        end_perf = time.perf_counter()
        span.end_time = datetime.now(timezone.utc)
        span.duration_ms = (end_perf - start_perf) * 1000.0
        trace_collector.record_span(span)
