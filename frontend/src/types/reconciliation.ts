export type ReconciliationSeverity = "INFO" | "WARNING" | "CRITICAL_MISMATCH";

export type ReconciliationStatus = "CLEAN" | "DRIFT_DETECTED" | "HALTED_ON_DISCREPANCY";

export type PositionDiscrepancyType =
  | "QUANTITY_MISMATCH"
  | "PHANTOM_INTERNAL"
  | "PHANTOM_BROKER"
  | "PRICE_MISMATCH";

export interface PositionDiscrepancy {
  symbol: string;
  internal_quantity: number;
  broker_quantity: number;
  quantity_diff: number;
  internal_avg_price: number;
  broker_avg_price: number;
  price_diff: number;
  discrepancy_type: PositionDiscrepancyType;
  severity: ReconciliationSeverity;
}

export interface CashDiscrepancy {
  internal_cash: number;
  broker_cash: number;
  cash_diff: number;
  diff_pct: number;
  severity: ReconciliationSeverity;
}

export interface OrderDiscrepancy {
  order_id: string;
  symbol: string;
  internal_status: string;
  broker_status: string;
  discrepancy_type: string;
}

export interface ReconciliationReport {
  report_id: string;
  account_id: string;
  broker_id: string;
  status: ReconciliationStatus;
  position_discrepancies: PositionDiscrepancy[];
  cash_discrepancy?: CashDiscrepancy | null;
  order_discrepancies: OrderDiscrepancy[];
  auto_halt_triggered: boolean;
  halt_reason?: string | null;
  reconciled_at: string;
}
