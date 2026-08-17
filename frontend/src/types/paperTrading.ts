export type PaperTradingSessionStatus = "INITIALIZED" | "ACTIVE" | "PAUSED" | "STOPPED" | "ERROR";

export interface PaperAccount {
  account_id: string;
  name: string;
  initial_balance: number;
  current_cash: number;
  margin_used: number;
  portfolio_value: number;
  currency: string;
  created_at: string;
}

export interface PaperOrderExecutionConfig {
  latency_ms: number;
  slippage_bps: number;
  partial_fills_enabled: boolean;
  fill_ratio: number;
}

export interface PaperTradingSession {
  session_id: string;
  strategy_id: string;
  account_id: string;
  status: PaperTradingSessionStatus;
  execution_config: PaperOrderExecutionConfig;
  symbols: string[];
  started_at: string;
  stopped_at?: string | null;
  total_trades: number;
  winning_trades: number;
  realized_pnl: number;
  unrealized_pnl: number;
  peak_portfolio_value: number;
  max_drawdown_pct: number;
}

export interface PaperTradingGateStatus {
  session_id: string;
  strategy_id: string;
  days_active: number;
  required_days: number;
  trades_count: number;
  required_trades: number;
  current_drawdown_pct: number;
  max_allowed_drawdown_pct: number;
  eligible_for_promotion: boolean;
  requirements_met: string[];
  requirements_pending: string[];
}
