import time
import pytest
from openquant.adapters.observability.telemetry import (
    get_correlation_id,
    set_correlation_id,
    trace_span,
    trace_collector,
)


def test_correlation_id_context():
    set_correlation_id("cid_custom_12345")
    assert get_correlation_id() == "cid_custom_12345"


def test_trace_span_recording_and_collector():
    trace_collector.clear()
    set_correlation_id("cid_test_trace_1")

    with trace_span("test_operation", {"user_id": "u123"}) as span:
        time.sleep(0.01)
        assert span.name == "test_operation"
        assert span.attributes["user_id"] == "u123"

    spans = trace_collector.get_recent_spans(limit=10)
    assert len(spans) == 1
    assert spans[0].name == "test_operation"
    assert spans[0].duration_ms >= 8.0
    assert spans[0].status == "OK"


def test_trace_span_captures_exceptions():
    trace_collector.clear()
    set_correlation_id("cid_test_error")

    with pytest.raises(ValueError, match="Synthetic failure"):
        with trace_span("faulty_operation", {"risk_check": True}):
            raise ValueError("Synthetic failure")

    spans = trace_collector.get_recent_spans(limit=10)
    assert len(spans) == 1
    assert spans[0].status == "ERROR"
    assert spans[0].error_message == "Synthetic failure"
