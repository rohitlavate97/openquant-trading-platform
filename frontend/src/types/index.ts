export type StrategyPromotionStage =
  | "DRAFT"
  | "SANDBOXED_CODE_REVIEW"
  | "BACKTEST"
  | "WALK_FORWARD_VALIDATION"
  | "PAPER_TRADING"
  | "HUMAN_APPROVAL"
  | "LIVE_TRADING";

export interface PromotionStageInfo {
  stage: StrategyPromotionStage;
  step_order: number;
  description: string;
}

export interface SystemInfo {
  platform: string;
  version: string;
  environment: string;
  debug: boolean;
  risk_engine: {
    kill_switch_active: boolean;
    max_daily_loss_percent: number;
    max_drawdown_percent: number;
    max_position_size_percent: number;
    max_orders_per_second: number;
  };
  sandbox: {
    max_cpu_seconds: number;
    max_memory_mb: number;
    execution_timeout_seconds: number;
    strict_allowlist_mode: boolean;
  };
  adapters: Array<{
    adapter_id: string;
    display_name: string;
    is_certified: boolean;
    is_live_trading_eligible: boolean;
  }>;
}

export interface HealthStatus {
  status: string;
  environment: string;
  version: string;
  registered_adapters_count: number;
  kill_switch_active: boolean;
  sandbox_strict_mode: boolean;
}
