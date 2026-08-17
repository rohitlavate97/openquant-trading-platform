export interface BacktestConfig {
  strategy_id: string;
  symbols: string[];
  start_date?: string;
  end_date?: string;
  timeframe?: string;
  initial_cash: number;
  slippage_bps: number;
  commission_per_order: number;
  parameters?: Record<string, unknown>;
}

export interface BacktestTrade {
  trade_id: string;
  symbol: string;
  side: string;
  entry_time: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  return_pct: number;
  commission_paid: number;
  holding_duration_seconds: number;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  cash: number;
  drawdown_pct: number;
}

export interface BacktestPerformanceMetrics {
  initial_equity: number;
  final_equity: number;
  total_net_profit: number;
  total_return_pct: number;
  cagr_pct: number;
  max_drawdown_pct: number;
  max_drawdown_dollars: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  profit_factor: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  average_trade_pnl: number;
  average_win: number;
  average_loss: number;
}

export interface BacktestResult {
  backtest_id: string;
  strategy_id: string;
  config: BacktestConfig;
  metrics: BacktestPerformanceMetrics;
  equity_curve: EquityPoint[];
  trades: BacktestTrade[];
  created_at: string;
}

export interface WalkForwardWindow {
  window_index: number;
  train_start: string;
  train_end: string;
  test_start: string;
  test_end: string;
  in_sample_metrics: BacktestPerformanceMetrics;
  out_of_sample_metrics: BacktestPerformanceMetrics;
  efficiency_ratio: number;
}

export interface WalkForwardResult {
  validation_id: string;
  strategy_id: string;
  num_windows: number;
  overall_efficiency_ratio: number;
  is_robust: boolean;
  overfitting_risk: "LOW" | "MEDIUM" | "HIGH";
  windows: WalkForwardWindow[];
  created_at: string;
}
