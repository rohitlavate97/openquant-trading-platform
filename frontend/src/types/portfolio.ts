export type PositionSide = "LONG" | "SHORT" | "FLAT";

export interface PortfolioPosition {
  account_id: string;
  symbol: string;
  side: PositionSide;
  quantity: number;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  allocation_pct: number;
  strategy_id?: string | null;
}

export interface AssetAllocationItem {
  symbol_or_class: string;
  market_value: number;
  percentage: number;
}

export interface PortfolioPerformanceSnapshot {
  timestamp: string;
  equity: number;
  drawdown_pct: number;
  daily_return_pct: number;
}

export interface PortfolioSummary {
  account_id: string;
  total_equity: number;
  cash_balance: number;
  margin_used: number;
  available_margin: number;
  unrealized_pnl: number;
  realized_pnl: number;
  daily_pnl: number;
  daily_pnl_pct: number;
  peak_equity: number;
  current_drawdown_pct: number;
  max_drawdown_pct: number;
  active_positions_count: number;
  win_rate_pct: number;
  profit_factor: number;
  sharpe_ratio: number;
  updated_at: string;
}
