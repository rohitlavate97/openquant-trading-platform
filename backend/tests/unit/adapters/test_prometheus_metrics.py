import pytest
from openquant.adapters.observability.prometheus_metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsRegistry,
)


def test_counter_increments_and_labels():
    counter = Counter("test_counter", "Test doc", ["method", "status"])
    counter.inc(1.0, method="POST", status="200")
    counter.inc(2.0, method="POST", status="200")
    counter.inc(1.0, method="GET", status="404")

    samples = counter.get_samples()
    assert len(samples) == 2
    post_sample = next(s for s in samples if s.labels.get("method") == "POST")
    assert post_sample.value == 3.0
    get_sample = next(s for s in samples if s.labels.get("method") == "GET")
    assert get_sample.value == 1.0


def test_gauge_set_inc_dec():
    gauge = Gauge("test_gauge", "Test doc", ["account"])
    gauge.set(100.0, account="ACC1")
    gauge.inc(25.0, account="ACC1")
    gauge.dec(10.0, account="ACC1")

    samples = gauge.get_samples()
    assert len(samples) == 1
    assert samples[0].value == 115.0


def test_histogram_observations_and_buckets():
    hist = Histogram("test_hist", "Test doc", ["op"], buckets=(0.01, 0.05, 0.1))
    hist.observe(0.005, op="order")
    hist.observe(0.03, op="order")
    hist.observe(0.2, op="order")

    samples = hist.get_samples()
    count_sample = next(s for s in samples if s.name == "test_hist_count")
    assert count_sample.value == 3.0
    sum_sample = next(s for s in samples if s.name == "test_hist_sum")
    assert pytest.approx(sum_sample.value, 0.001) == 0.235


def test_metrics_registry_prometheus_text_format():
    reg = MetricsRegistry()
    reg.orders_total.inc(1.0, status="FILLED", broker_id="ib", symbol="AAPL")
    reg.kill_switch_status.set(1.0, level="GLOBAL")

    text = reg.generate_prometheus_text()
    assert "# HELP openquant_orders_total" in text
    assert "# TYPE openquant_orders_total counter" in text
    assert 'openquant_orders_total{broker_id="ib",status="FILLED",symbol="AAPL"} 1.0' in text
    assert 'openquant_kill_switch_active{level="GLOBAL"} 1.0' in text
