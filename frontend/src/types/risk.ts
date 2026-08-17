export type KillSwitchLevel = "GLOBAL" | "ACCOUNT" | "STRATEGY" | "SYMBOL";

export interface KillSwitchState {
  is_active: boolean;
  level: KillSwitchLevel;
  target_id?: string | null;
  activated_by?: string | null;
  activated_at?: string | null;
  reason?: string | null;
  positions_flattened: boolean;
}

export interface RiskLimitsConfig {
  max_daily_loss_percent: number;
  max_drawdown_percent: number;
  max_single_trade_risk_percent: number;
  max_position_size_percent: number;
  max_orders_per_second: number;
  max_open_orders_per_symbol: number;
  self_trade_prevention: boolean;
  kill_switch: KillSwitchState;
}

export interface RiskCheckResult {
  check_type: string;
  passed: boolean;
  severity: "BLOCKING" | "WARNING";
  rule_name: string;
  message: string;
  details: Record<string, any>;
}

export interface RiskEvaluationResult {
  allowed: boolean;
  checks: RiskCheckResult[];
  rejection_reasons: string[];
  evaluated_at?: string;
}
