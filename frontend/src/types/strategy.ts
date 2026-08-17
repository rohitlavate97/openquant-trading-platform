export type StrategyState =
  | "DRAFT"
  | "INITIALIZED"
  | "RUNNING"
  | "PAUSED"
  | "STOPPED"
  | "ERROR";

export type ParameterType = "INT" | "FLOAT" | "STRING" | "BOOLEAN";

export interface StrategyParameter {
  name: string;
  param_type: ParameterType;
  default_value: any;
  current_value: any;
  min_value?: number | null;
  max_value?: number | null;
  description?: string;
}

export interface StrategySignal {
  symbol: string;
  signal_type: string;
  confidence: number;
  suggested_quantity?: number | string | null;
  suggested_price?: number | string | null;
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface Strategy {
  strategy_id: string;
  name: string;
  description: string;
  author_id: string;
  source_code: string;
  parameters: StrategyParameter[];
  promotion_stage: string;
  state: StrategyState;
  symbols: string[];
  timeframes: string[];
  account_id: string;
  broker_id: string;
  total_trades: number;
  winning_trades: number;
  total_pnl: string | number;
  created_at: string;
  updated_at: string;
}
