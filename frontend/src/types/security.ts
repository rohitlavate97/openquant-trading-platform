export interface SecurityCheckResult {
  check_id: string;
  name: string;
  category: "SANDBOX" | "SECRETS" | "OMS" | "WEBHOOK" | "RISK";
  status: "PASSED" | "FAILED";
  latency_ms: number;
  details: string;
}

export interface SecurityAuditReport {
  report_id: string;
  generated_at: string;
  overall_status: "CERTIFIED" | "VULNERABLE";
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  security_score_percent: number;
  total_duration_ms: number;
  checks: SecurityCheckResult[];
}
