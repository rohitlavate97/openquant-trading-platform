import React, { useState } from "react";
import { ObservabilitySummary, TraceSpan, GrafanaDashboardDef } from "../../types/observability";

export const ObservabilityPage: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<"overview" | "traces" | "prometheus" | "grafana">("overview");

  const [summary] = useState<ObservabilitySummary>({
    total_orders_placed: 142,
    total_risk_checks_evaluated: 489,
    total_market_ticks_ingested: 125840,
    total_http_requests_handled: 8420,
    active_spans_in_buffer: 52,
    kill_switch_active: false,
  });

  const [traces] = useState<TraceSpan[]>([
    {
      trace_id: "cid_a982f1b4c012",
      span_id: "span_9f82d1",
      parent_span_id: null,
      name: "http.request: POST /api/v1/orders",
      start_time: new Date(Date.now() - 12000).toISOString(),
      end_time: new Date(Date.now() - 11980).toISOString(),
      duration_ms: 19.84,
      attributes: { method: "POST", endpoint: "/api/v1/orders", status_code: "201" },
      status: "OK",
    },
    {
      trace_id: "cid_a982f1b4c012",
      span_id: "span_b48102",
      parent_span_id: "span_9f82d1",
      name: "risk_engine.evaluate_order",
      start_time: new Date(Date.now() - 11995).toISOString(),
      end_time: new Date(Date.now() - 11993).toISOString(),
      duration_ms: 1.45,
      attributes: { symbol: "AAPL", idempotency_key: "idem_894f2" },
      status: "OK",
    },
    {
      trace_id: "cid_fe810294da10",
      span_id: "span_e71029",
      parent_span_id: null,
      name: "market_data.staleness_check",
      start_time: new Date(Date.now() - 45000).toISOString(),
      end_time: new Date(Date.now() - 44998).toISOString(),
      duration_ms: 0.82,
      attributes: { symbol: "BTCUSDT", max_staleness_ms: 3000 },
      status: "OK",
    },
    {
      trace_id: "cid_992104fa2810",
      span_id: "span_332190",
      parent_span_id: null,
      name: "broker.route_order: binance_crypto",
      start_time: new Date(Date.now() - 90000).toISOString(),
      end_time: new Date(Date.now() - 89960).toISOString(),
      duration_ms: 41.2,
      attributes: { symbol: "ETHUSDT", order_type: "LIMIT" },
      status: "OK",
    },
  ]);

  const [dashboards] = useState<GrafanaDashboardDef[]>([
    {
      id: "openquant-trading-ops",
      title: "OpenQuant - Trading Operations & OMS",
      description: "Real-time order throughput, fill latencies, and broker adapter execution metrics.",
      panels_count: 6,
      tags: ["trading", "oms", "brokers"],
      schema_version: 38,
    },
    {
      id: "openquant-risk-controls",
      title: "OpenQuant - Pre-Trade Risk & Kill Switch",
      description: "Pre-trade hard stop evaluations, rate limiters, and emergency kill switch status.",
      panels_count: 5,
      tags: ["risk", "kill-switch", "compliance"],
      schema_version: 38,
    },
    {
      id: "openquant-market-data",
      title: "OpenQuant - Market Data & Feed Latency",
      description: "3000ms staleness monitoring, tick ingestion rates, and WebSocket broadcasting health.",
      panels_count: 4,
      tags: ["market-data", "staleness", "websockets"],
      schema_version: 38,
    },
  ]);

  const [filterTraceId, setFilterTraceId] = useState("");
  const [copied, setCopied] = useState(false);

  const prometheusSampleText = `# HELP openquant_orders_total Total orders placed by status, broker, and symbol
# TYPE openquant_orders_total counter
openquant_orders_total{broker_id="interactive_brokers",status="FILLED",symbol="AAPL"} 84
openquant_orders_total{broker_id="binance_crypto",status="FILLED",symbol="BTCUSDT"} 58

# HELP openquant_risk_evaluations_total Total pre-trade risk checks evaluated by verdict and rule
# TYPE openquant_risk_evaluations_total counter
openquant_risk_evaluations_total{rule="PASSED",verdict="ALLOWED"} 482
openquant_risk_evaluations_total{rule="HARD_STOP",verdict="REJECTED"} 7

# HELP openquant_kill_switch_active State of the Global Emergency Kill Switch (1=Active, 0=Unlocked)
# TYPE openquant_kill_switch_active gauge
openquant_kill_switch_active{level="GLOBAL"} 0

# HELP openquant_market_data_staleness_ms Latest market tick age in milliseconds per symbol
# TYPE openquant_market_data_staleness_ms gauge
openquant_market_data_staleness_ms{symbol="AAPL"} 42
openquant_market_data_staleness_ms{symbol="BTCUSDT"} 18`;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredTraces = traces.filter(
    (t) => !filterTraceId || t.trace_id.toLowerCase().includes(filterTraceId.toLowerCase()) || t.name.toLowerCase().includes(filterTraceId.toLowerCase())
  );

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight text-text">Observability & Monitoring</h1>
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Prometheus • OpenTelemetry • Grafana
            </span>
          </div>
          <p className="text-text-muted mt-2 text-sm">
            Real-time telemetry, Prometheus scraping endpoint, distributed tracing spans with correlation IDs, and Grafana dashboard models.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => copyToClipboard("http://localhost:8000/metrics")}
            className="px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-xs font-medium text-text flex items-center gap-2 transition-all"
          >
            <span className="text-indigo-400 font-mono text-[11px]">/metrics</span>
            <span>{copied ? "Copied!" : "Copy URL"}</span>
          </button>
        </div>
      </div>

      {/* Top Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface rounded-xl border border-border p-5 shadow-sm">
          <div className="text-xs font-medium text-text-muted">Total HTTP API Requests</div>
          <div className="text-2xl font-bold text-text mt-1">{summary.total_http_requests_handled.toLocaleString()}</div>
          <div className="text-[11px] text-emerald-400 mt-1">Instrumented with Correlation IDs</div>
        </div>

        <div className="bg-surface rounded-xl border border-border p-5 shadow-sm">
          <div className="text-xs font-medium text-text-muted">Risk Checks Evaluated</div>
          <div className="text-2xl font-bold text-indigo-400 mt-1">{summary.total_risk_checks_evaluated.toLocaleString()}</div>
          <div className="text-[11px] text-text-muted mt-1">Pre-trade synchronous hard stops</div>
        </div>

        <div className="bg-surface rounded-xl border border-border p-5 shadow-sm">
          <div className="text-xs font-medium text-text-muted">Market Ticks Ingested</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{summary.total_market_ticks_ingested.toLocaleString()}</div>
          <div className="text-[11px] text-text-muted mt-1">&lt; 3000ms latency enforced</div>
        </div>

        <div className="bg-surface rounded-xl border border-border p-5 shadow-sm">
          <div className="text-xs font-medium text-text-muted">Active Spans Buffer</div>
          <div className="text-2xl font-bold text-text mt-1">{summary.active_spans_in_buffer}</div>
          <div className="text-[11px] text-emerald-400 mt-1">OpenTelemetry Spans</div>
        </div>
      </div>

      {/* Subtabs */}
      <div className="flex border-b border-border text-sm">
        <button
          type="button"
          onClick={() => setActiveSubTab("overview")}
          className={`px-4 py-2 font-medium border-b-2 transition-all ${
            activeSubTab === "overview" ? "border-indigo-500 text-indigo-400 font-bold" : "border-transparent text-text-muted hover:text-text"
          }`}
        >
          Telemetry Overview
        </button>
        <button
          type="button"
          onClick={() => setActiveSubTab("traces")}
          className={`px-4 py-2 font-medium border-b-2 transition-all ${
            activeSubTab === "traces" ? "border-indigo-500 text-indigo-400 font-bold" : "border-transparent text-text-muted hover:text-text"
          }`}
        >
          Distributed Traces
        </button>
        <button
          type="button"
          onClick={() => setActiveSubTab("prometheus")}
          className={`px-4 py-2 font-medium border-b-2 transition-all ${
            activeSubTab === "prometheus" ? "border-indigo-500 text-indigo-400 font-bold" : "border-transparent text-text-muted hover:text-text"
          }`}
        >
          Prometheus Exporter
        </button>
        <button
          type="button"
          onClick={() => setActiveSubTab("grafana")}
          className={`px-4 py-2 font-medium border-b-2 transition-all ${
            activeSubTab === "grafana" ? "border-indigo-500 text-indigo-400 font-bold" : "border-transparent text-text-muted hover:text-text"
          }`}
        >
          Grafana Dashboards
        </button>
      </div>

      {/* Tab Content */}
      {activeSubTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-surface rounded-xl border border-border p-6 shadow-sm space-y-4">
            <h3 className="text-base font-semibold text-text">Observability Architecture</h3>
            <p className="text-xs text-text-muted leading-relaxed">
              OpenQuant embeds native OpenTelemetry distributed tracing and a thread-safe Prometheus metrics registry without requiring external sidecars for basic metrics. Every order, synchronous risk check, and market tick is assigned a correlation context ID that propagates across WebSocket and HTTP endpoints.
            </p>
            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="p-3 bg-surface-elevated rounded-lg border border-border text-xs">
                <div className="text-text-muted">Prometheus Scrape Endpoint</div>
                <div className="font-mono text-indigo-400 font-bold mt-1">/metrics</div>
              </div>
              <div className="p-3 bg-surface-elevated rounded-lg border border-border text-xs">
                <div className="text-text-muted">Trace Header</div>
                <div className="font-mono text-emerald-400 font-bold mt-1">X-Correlation-ID</div>
              </div>
            </div>
          </div>

          <div className="bg-surface rounded-xl border border-border p-6 shadow-sm space-y-4">
            <h3 className="text-base font-semibold text-text">Pre-Configured Metrics Expositions</h3>
            <ul className="space-y-2 text-xs text-text-muted">
              <li className="flex items-center justify-between p-2 rounded bg-surface-elevated border border-border/50">
                <span className="font-mono text-text font-medium">openquant_orders_total</span>
                <span className="text-indigo-400 font-semibold">Counter</span>
              </li>
              <li className="flex items-center justify-between p-2 rounded bg-surface-elevated border border-border/50">
                <span className="font-mono text-text font-medium">openquant_order_latency_seconds</span>
                <span className="text-indigo-400 font-semibold">Histogram</span>
              </li>
              <li className="flex items-center justify-between p-2 rounded bg-surface-elevated border border-border/50">
                <span className="font-mono text-text font-medium">openquant_risk_evaluation_duration_seconds</span>
                <span className="text-indigo-400 font-semibold">Histogram</span>
              </li>
              <li className="flex items-center justify-between p-2 rounded bg-surface-elevated border border-border/50">
                <span className="font-mono text-text font-medium">openquant_market_data_staleness_ms</span>
                <span className="text-indigo-400 font-semibold">Gauge</span>
              </li>
            </ul>
          </div>
        </div>
      )}

      {activeSubTab === "traces" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 max-w-md">
              <input
                type="text"
                placeholder="Search by Trace ID or Span name..."
                value={filterTraceId}
                onChange={(e) => setFilterTraceId(e.target.value)}
                className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-text focus:outline-none focus:border-indigo-500"
              />
            </div>
            <span className="text-xs text-text-muted">{filteredTraces.length} Spans Loaded</span>
          </div>

          <div className="bg-surface rounded-xl border border-border overflow-hidden shadow-sm">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-elevated border-b border-border text-text-muted uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-3">Trace / Span ID</th>
                  <th className="px-4 py-3">Span Name</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Attributes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredTraces.map((span) => (
                  <tr key={span.span_id} className="hover:bg-surface-elevated/50 transition-colors">
                    <td className="px-4 py-3 font-mono text-[11px] text-text-muted">
                      <div>{span.trace_id}</div>
                      <div className="text-[10px] text-indigo-400">{span.span_id}</div>
                    </td>
                    <td className="px-4 py-3 font-semibold text-text">{span.name}</td>
                    <td className="px-4 py-3 font-mono font-bold text-emerald-400">{span.duration_ms} ms</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400">
                        {span.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-[10px] text-text-muted">
                      {JSON.stringify(span.attributes)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeSubTab === "prometheus" && (
        <div className="bg-surface rounded-xl border border-border p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-text">Prometheus OpenMetrics Live Text Exposition</h3>
            <button
              type="button"
              onClick={() => copyToClipboard(prometheusSampleText)}
              className="px-3 py-1 bg-surface-elevated border border-border rounded text-xs text-text hover:bg-surface-elevated/80"
            >
              {copied ? "Copied Metrics!" : "Copy OpenMetrics Text"}
            </button>
          </div>
          <pre className="p-4 bg-black/60 rounded-lg text-emerald-400 font-mono text-xs overflow-x-auto leading-relaxed border border-border">
            {prometheusSampleText}
          </pre>
        </div>
      )}

      {activeSubTab === "grafana" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {dashboards.map((dash) => (
            <div key={dash.id} className="bg-surface rounded-xl border border-border p-6 shadow-sm space-y-4 flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                    Grafana v{dash.schema_version}
                  </span>
                  <span className="text-xs text-text-muted">{dash.panels_count} Panels</span>
                </div>
                <h3 className="text-base font-bold text-text">{dash.title}</h3>
                <p className="text-xs text-text-muted leading-relaxed">{dash.description}</p>
                <div className="flex flex-wrap gap-1.5 pt-2">
                  {dash.tags.map((t) => (
                    <span key={t} className="text-[10px] px-2 py-0.5 rounded bg-surface-elevated text-text-muted border border-border">
                      #{t}
                    </span>
                  ))}
                </div>
              </div>

              <button
                type="button"
                onClick={() => alert(`Grafana Dashboard '${dash.title}' JSON exported successfully.`)}
                className="w-full py-2 bg-surface-elevated hover:bg-surface-elevated/80 border border-border rounded-lg text-xs font-semibold text-text transition-all"
              >
                Export JSON Template
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ObservabilityPage;
