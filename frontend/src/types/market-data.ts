export type FeedHealthStatus = "HEALTHY" | "DEGRADED" | "STALE" | "DISCONNECTED";

export interface SymbolFeedMetrics {
  symbol: string;
  feed_status: FeedHealthStatus;
  last_tick_timestamp: string;
  age_ms: number;
  is_stale: boolean;
  total_ticks_received: number;
  tick_frequency_per_sec: number;
}

export interface MarketDataStalenessReport {
  overall_status: FeedHealthStatus;
  max_staleness_ms: number;
  is_trading_paused: boolean;
  stale_symbols_count: number;
  symbols: Record<string, SymbolFeedMetrics>;
  timestamp: string;
}

export interface CandleData {
  symbol: string;
  timeframe: string;
  timestamp: string;
  open: number | string;
  high: number | string;
  low: number | string;
  close: number | string;
  volume: number | string;
}
