export type TradingViewAction = "BUY" | "SELL" | "CLOSE" | "CANCEL";

export interface TradingViewWebhookPayload {
  strategy_id: string;
  account_id: string;
  broker_id?: string;
  ticker: string;
  action: TradingViewAction;
  contracts: number;
  price?: number | null;
  order_type?: string;
  nonce: string;
  timestamp: number;
  signature?: string | null;
  passphrase?: string | null;
}

export interface TradingViewWebhookResult {
  success: boolean;
  order_id?: string | null;
  message: string;
  executed_at: string;
}

export type MT5ConnectionState =
  | "DISCONNECTED"
  | "CONNECTING"
  | "CONNECTED"
  | "HEARTBEAT_TIMEOUT"
  | "ERROR";

export interface MT5BridgeStatus {
  state: MT5ConnectionState;
  connected_eas_count: number;
  last_heartbeat?: string | null;
  messages_processed: number;
  latency_ms: number;
}

export interface MT5BridgeCommand {
  command_id: string;
  action: string;
  symbol: string;
  volume: number;
  price?: number | null;
  sl?: number | null;
  tp?: number | null;
  comment?: string;
}

export type SheetsSignalType = "BUY" | "SELL" | "CLOSE";

export interface SheetsStrategyRow {
  row_index: number;
  timestamp: string;
  symbol: string;
  signal_type: SheetsSignalType;
  quantity: number;
  limit_price?: number | null;
  stop_loss?: number | null;
  take_profit?: number | null;
  strategy_tag: string;
  is_valid: boolean;
  validation_error?: string | null;
}

export interface SheetsParseResult {
  total_rows: number;
  valid_rows_count: number;
  invalid_rows_count: number;
  rows: SheetsStrategyRow[];
  parsed_orders: Array<{
    symbol: string;
    side: string;
    quantity: number;
    limit_price?: number | null;
    strategy_tag: string;
  }>;
}
