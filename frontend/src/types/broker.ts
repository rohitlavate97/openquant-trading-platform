export interface BrokerSecurityAuditCheck {
  check_name: string;
  passed: boolean;
  description: string;
  details?: Record<string, any>;
}

export interface BrokerSecurityAuditReport {
  adapter_id: string;
  is_certified: boolean;
  live_trading_eligible: boolean;
  audit_timestamp: string;
  certified_by?: string | null;
  checks: BrokerSecurityAuditCheck[];
  rejection_reasons: string[];
}

export interface BrokerAdapterMetadata {
  adapter_id: string;
  display_name: string;
  version: string;
  supported_asset_classes: string[];
  supported_order_types: string[];
  is_certified: boolean;
  is_live_trading_eligible: boolean;
  certification_report?: BrokerSecurityAuditReport | null;
}

export interface BrokerAccountInfo {
  account_id: string;
  broker_id: string;
  currency: string;
  total_balance: number | string;
  available_cash: number | string;
  margin_used: number | string;
  collateral: number | string;
}
