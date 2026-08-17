export interface ObservabilitySummary {
  total_orders_placed: number;
  total_risk_checks_evaluated: number;
  total_market_ticks_ingested: number;
  total_http_requests_handled: number;
  active_spans_in_buffer: number;
  kill_switch_active: boolean;
}

export interface TraceSpan {
  trace_id: string;
  span_id: string;
  parent_span_id: string | null;
  name: string;
  start_time: string;
  end_time: string | null;
  duration_ms: number;
  attributes: Record<string, any>;
  status: "OK" | "ERROR";
  error_message?: string | null;
}

export interface GrafanaDashboardDef {
  id: string;
  title: string;
  description: string;
  panels_count: number;
  tags: string[];
  schema_version: number;
}
