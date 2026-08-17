export type AIReviewStatus =
  | "PENDING_HUMAN_REVIEW"
  | "APPROVED_BY_HUMAN"
  | "REJECTED_BY_HUMAN";

export interface AICodeGenerationRequest {
  prompt: string;
  strategy_name?: string;
  strategy_type?: string;
  symbols?: string[];
}

export interface AICodeGenerationResult {
  generation_id: string;
  strategy_name: string;
  code: string;
  description: string;
  parameters: Array<{
    name: string;
    type: string;
    default: any;
    description: string;
  }>;
  ast_safety_passed: boolean;
  ast_violations: string[];
  review_status: AIReviewStatus;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  advisory_disclaimer: string;
  generated_at: string;
}

export type AIAnomalySeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface AIAnomalyItem {
  anomaly_id: string;
  category: string;
  severity: AIAnomalySeverity;
  summary: string;
  root_cause: string;
  recommended_action: string;
}

export interface AILogAnalysisReport {
  report_id: string;
  total_events_analyzed: number;
  health_score: number;
  anomalies: AIAnomalyItem[];
  summary: string;
  generated_at: string;
}

export interface AIRiskRecommendation {
  parameter_name: string;
  current_value: any;
  suggested_value: any;
  rationale: string;
}

export interface AIRiskAdviceReport {
  report_id: string;
  plain_english_explanation: string;
  breach_category: string;
  recommended_actions: AIRiskRecommendation[];
  safety_score_impact: string;
  generated_at: string;
}
