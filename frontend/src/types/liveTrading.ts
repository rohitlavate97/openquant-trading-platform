export type LiveTradingState = "READY" | "PREFLIGHT_CHECKING" | "ACTIVE" | "HALTED" | "TERMINATED";

export type ScalingTier = "TIER_1_STARTER" | "TIER_2_INTERMEDIATE" | "TIER_3_FULL";

export interface LiveCapitalAllocation {
  strategy_id: string;
  broker_id: string;
  account_id: string;
  total_authorized_capital: string;
  scaling_tier: ScalingTier;
  max_order_notional: string;
  margin_floor_buffer: string;
  max_daily_loss: string;
  max_drawdown_percent: string;
  effective_allocated_capital?: string;
}

export interface LivePreflightCheckItem {
  check_name: string;
  passed: boolean;
  description: string;
  details?: Record<string, any>;
  is_blocking: boolean;
}

export interface LivePreflightReport {
  strategy_id: string;
  broker_id: string;
  account_id: string;
  is_eligible: boolean;
  checked_at: string;
  checks: LivePreflightCheckItem[];
  rejection_reasons: string[];
}

export interface LiveStrategySession {
  session_id: string;
  strategy_id: string;
  strategy_name: string;
  broker_id: string;
  account_id: string;
  allocation: LiveCapitalAllocation;
  state: LiveTradingState;
  activated_by: string;
  confirmed_by?: string;
  activated_at?: string;
  deactivated_at?: string;
  halt_reason?: string;
  preflight_report?: LivePreflightReport;
  realized_pnl: string;
  unrealized_pnl: string;
  live_orders_count: number;
}
