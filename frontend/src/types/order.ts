export type OrderSide = "BUY" | "SELL";
export type OrderType = "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT";
export type OrderStatus =
  | "PENDING_RISK_CHECK"
  | "RISK_REJECTED"
  | "PENDING_SUBMISSION"
  | "SUBMITTED"
  | "OPEN"
  | "PARTIALLY_FILLED"
  | "FILLED"
  | "CANCELLED"
  | "REJECTED"
  | "EXPIRED";

export type PositionSide = "LONG" | "SHORT" | "FLAT";

export interface OrderItem {
  order_id: string;
  idempotency_key: string;
  strategy_id: string;
  account_id: string;
  broker_id: string;
  broker_order_id?: string | null;
  symbol: string;
  side: OrderSide;
  order_type: OrderType;
  status: OrderStatus;
  quantity: number | string;
  filled_quantity: number | string;
  price?: number | string | null;
  stop_price?: number | string | null;
  average_fill_price?: number | string | null;
  rejection_reason?: string | null;
  created_at: string;
  updated_at: string;
  tag?: string | null;
}

export interface PositionItem {
  position_id: string;
  account_id: string;
  strategy_id: string;
  broker_id: string;
  symbol: string;
  side: PositionSide;
  quantity: number | string;
  entry_price: number | string;
  current_price: number | string;
  unrealized_pnl: number | string;
  realized_pnl: number | string;
  updated_at: string;
}

export interface PositionReconciliationItem {
  symbol: string;
  internal_quantity: number | string;
  broker_quantity: number | string;
  quantity_delta: number | string;
  is_reconciled: boolean;
  status: string;
}

export interface PositionReconciliationReport {
  account_id: string;
  broker_id: string;
  is_fully_reconciled: boolean;
  discrepancy_count: number;
  items: PositionReconciliationItem[];
  timestamp: string;
}
