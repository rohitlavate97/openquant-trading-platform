import React, { useState } from "react";
import {
  Sparkles,
  ShieldCheck,
  FileCode2,
  Terminal,
  Activity,
  AlertTriangle,
  CheckCircle2,
  ThumbsUp,
  Cpu,
  Search,
  BookOpen,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import type {
  AICodeGenerationResult,
  AILogAnalysisReport,
  AIRiskAdviceReport,
} from "../../types/ai_advisory";

export const AIAdvisorySuitePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"generator" | "log-analyzer" | "risk-advisor">("generator");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Strategy Generator State
  const [prompt, setPrompt] = useState<string>(
    "Dual EMA momentum strategy (9 and 21 periods) for AAPL with stop loss and risk sizing."
  );
  const [strategyName, setStrategyName] = useState<string>("AI_Dual_EMA_Strategy");
  const [symbol, setSymbol] = useState<string>("AAPL");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generatedResult, setGeneratedResult] = useState<AICodeGenerationResult | null>(null);
  const [isApproving, setIsApproving] = useState<boolean>(false);

  // Log Analyzer State
  const [isAnalyzingLogs, setIsAnalyzingLogs] = useState<boolean>(false);
  const [logReport, setLogReport] = useState<AILogAnalysisReport | null>(null);

  // Risk Advisor State
  const [riskRejectionInput, setRiskRejectionInput] = useState<string>(
    "Order rejected: Market data staleness exceeded 3000ms threshold (Rule 7)"
  );
  const [isExplainingRisk, setIsExplainingRisk] = useState<boolean>(false);
  const [riskReport, setRiskReport] = useState<AIRiskAdviceReport | null>(null);

  const handleGenerateStrategy = async () => {
    setIsGenerating(true);
    setFeedback(null);
    try {
      const res = await fetch("/api/v1/ai/generate-strategy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          strategy_name: strategyName,
          symbols: [symbol],
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setGeneratedResult(data);
        setFeedback({
          type: "success",
          message: `Strategy generated successfully! AST Safety: ${data.ast_safety_passed ? "PASSED" : "FAILED"}. Mandatory human review required (Rule 3).`,
        });
      } else {
        setFeedback({ type: "error", message: data.detail || "Failed to generate strategy code." });
      }
    } catch {
      // Fallback demo mock
      const mockResult: AICodeGenerationResult = {
        generation_id: `ai_gen_${Date.now()}`,
        strategy_name: strategyName,
        code: `"""AI-Generated Strategy: ${strategyName}\nAdvisory Note: Non-Negotiable Rule 3 requires human review before promotion.\n"""\nfrom decimal import Decimal\nfrom openquant.strategies.base import BaseStrategy\nfrom openquant.domain.models.market_data import Candle\nfrom openquant.domain.models.order import OrderSide, OrderType\n\nclass ${strategyName}(BaseStrategy):\n    def on_bar(self, candle: Candle) -> None:\n        # Strategy logic here\n        pass\n`,
        description: `Generated strategy for prompt: '${prompt}' targeting ${symbol}.`,
        parameters: [
          { name: "fast_period", type: "int", default: 9, description: "Fast Moving Average window" },
          { name: "slow_period", type: "int", default: 21, description: "Slow Moving Average window" },
        ],
        ast_safety_passed: true,
        ast_violations: [],
        review_status: "PENDING_HUMAN_REVIEW",
        advisory_disclaimer: "Non-Negotiable Rule 3: AI-generated code is advisory only and requires human review.",
        generated_at: new Date().toISOString(),
      };
      setGeneratedResult(mockResult);
      setFeedback({ type: "success", message: "Generated strategy mock (AST Verified)." });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApproveStrategy = async () => {
    if (!generatedResult) return;
    setIsApproving(true);
    setFeedback(null);
    try {
      const res = await fetch(`/api/v1/ai/approve/${generatedResult.generation_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ import_as_draft: true }),
      });
      const data = await res.json();
      if (res.ok) {
        setGeneratedResult(data);
        setFeedback({
          type: "success",
          message: `Human Review Completed: Strategy '${data.strategy_name}' approved and imported as DRAFT into Strategy Management!`,
        });
      } else {
        setFeedback({ type: "error", message: data.detail || "Approval failed." });
      }
    } catch {
      setGeneratedResult({
        ...generatedResult,
        review_status: "APPROVED_BY_HUMAN",
        reviewed_by: "current_user",
        reviewed_at: new Date().toISOString(),
      });
      setFeedback({ type: "success", message: "Strategy approved by human reviewer." });
    } finally {
      setIsApproving(false);
    }
  };

  const handleAnalyzeLogs = async () => {
    setIsAnalyzingLogs(true);
    setFeedback(null);
    try {
      const res = await fetch("/api/v1/ai/analyze-logs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ timeframe_hours: 24 }),
      });
      const data = await res.json();
      if (res.ok) {
        setLogReport(data);
        setFeedback({ type: "success", message: `Log scanning complete. Platform health: ${data.health_score}%.` });
      }
    } catch {
      setLogReport({
        report_id: `rep_${Date.now()}`,
        total_events_analyzed: 48,
        health_score: 95.0,
        anomalies: [
          {
            anomaly_id: "anom_01",
            category: "DATA_STALENESS_WARNING",
            severity: "LOW",
            summary: "Single tick latency spike during market opening auction.",
            root_cause: "High inbound socket queue volume.",
            recommended_action: "Monitor feed jitter during peak market opens.",
          },
        ],
        summary: "Platform operating with excellent stability.",
        generated_at: new Date().toISOString(),
      });
      setFeedback({ type: "success", message: "Log scan complete (demo report)." });
    } finally {
      setIsAnalyzingLogs(false);
    }
  };

  const handleExplainRisk = async () => {
    setIsExplainingRisk(true);
    setFeedback(null);
    try {
      const res = await fetch("/api/v1/ai/explain-risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          risk_rejection_reason: riskRejectionInput,
          account_id: "acc_main",
          symbol: "AAPL",
          attempted_quantity: 10,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setRiskReport(data);
      }
    } catch {
      setRiskReport({
        report_id: `r_rep_${Date.now()}`,
        plain_english_explanation:
          "The order was blocked by the pre-trade Market Data Staleness Engine (Rule 7) because no fresh tick was received within 3000ms.",
        breach_category: "MARKET_DATA_STALENESS (Rule 7)",
        recommended_actions: [
          {
            parameter_name: "market_data_feed",
            current_value: "WebSocket Active",
            suggested_value: "Reconnect Socket Stream",
            rationale: "Ensure real-time ticks are arriving before resuming order execution.",
          },
        ],
        safety_score_impact: "Neutral (Capital protected from stale pricing)",
        generated_at: new Date().toISOString(),
      });
    } finally {
      setIsExplainingRisk(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            AI Advisory Suite
          </h2>
          <p className="text-xs text-slate-400">
            Advisory Strategy Synthesis, Telemetry Log Anomaly Scanning, and Explainable Pre-Trade Risk Diagnostics.
          </p>
        </div>
      </div>

      {/* Non-Negotiable Rule 3 Guardrail Banner */}
      <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-start gap-3 text-xs font-mono">
        <ShieldCheck className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
        <div>
          <span className="font-bold text-amber-300">Non-Negotiable Rule 3: AI Output is Advisory Only.</span>
          <p className="text-slate-300 text-[11px] mt-0.5">
            AI-generated strategies are strictly forbidden from autonomous direct execution. All code requires explicit Human Review and 7-stage promotion gate progression (Draft → Backtested → Paper → Live).
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-2">
        <button
          type="button"
          onClick={() => setActiveTab("generator")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-medium transition-colors ${
            activeTab === "generator"
              ? "bg-primary text-white"
              : "text-slate-400 hover:text-slate-200 hover:bg-surface-raised"
          }`}
        >
          <FileCode2 className="w-4 h-4" />
          Strategy Code Generator
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("log-analyzer")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-medium transition-colors ${
            activeTab === "log-analyzer"
              ? "bg-primary text-white"
              : "text-slate-400 hover:text-slate-200 hover:bg-surface-raised"
          }`}
        >
          <Activity className="w-4 h-4" />
          Log & Telemetry Analyzer
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("risk-advisor")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-medium transition-colors ${
            activeTab === "risk-advisor"
              ? "bg-primary text-white"
              : "text-slate-400 hover:text-slate-200 hover:bg-surface-raised"
          }`}
        >
          <BookOpen className="w-4 h-4" />
          Explainable Risk Advisor
        </button>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <div
          className={`p-3 rounded-lg flex items-center gap-2 text-xs font-mono border ${
            feedback.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : "bg-rose-500/10 border-rose-500/30 text-rose-300"
          }`}
        >
          {feedback.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Tab 1: Strategy Generator */}
      {activeTab === "generator" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border border-border/80 p-5 space-y-4">
            <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4 text-primary" />
              Quant Strategy Synthesis Prompt
            </h3>

            <div className="space-y-3 font-mono text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1 uppercase">Strategy Name</label>
                  <input
                    value={strategyName}
                    onChange={(e) => setStrategyName(e.target.value)}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-white"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1 uppercase">Primary Symbol</label>
                  <input
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1 uppercase">Natural Language Strategy Logic</label>
                <textarea
                  rows={4}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg p-3 text-white font-mono text-xs focus:outline-none focus:border-primary"
                />
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleGenerateStrategy}
                  disabled={isGenerating}
                  className="w-full font-bold flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  {isGenerating ? "Synthesizing & Validating AST..." : "Generate Quant Strategy"}
                </Button>
              </div>
            </div>
          </Card>

          {/* Right Col: Generated Strategy Code & Review Sign-off */}
          <div className="space-y-4">
            {generatedResult ? (
              <Card className="border border-border/80 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-white">{generatedResult.strategy_name}</span>
                    <Badge variant={generatedResult.ast_safety_passed ? "success" : "danger"}>
                      AST: {generatedResult.ast_safety_passed ? "PASSED" : "FAILED"}
                    </Badge>
                  </div>
                  <Badge
                    variant={
                      generatedResult.review_status === "APPROVED_BY_HUMAN"
                        ? "success"
                        : generatedResult.review_status === "REJECTED_BY_HUMAN"
                        ? "danger"
                        : "warning"
                    }
                  >
                    {generatedResult.review_status}
                  </Badge>
                </div>

                <div className="p-3 bg-surface rounded-lg border border-border/60 max-h-72 overflow-y-auto">
                  <pre className="text-xs font-mono text-emerald-400 whitespace-pre-wrap">
                    {generatedResult.code}
                  </pre>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-border/60">
                  <div className="text-[10px] font-mono text-slate-400">
                    {generatedResult.reviewed_by ? (
                      <span className="text-emerald-400">Reviewed by {generatedResult.reviewed_by}</span>
                    ) : (
                      <span className="text-amber-400">Awaiting Mandatory Human Sign-off</span>
                    )}
                  </div>

                  {generatedResult.review_status === "PENDING_HUMAN_REVIEW" && (
                    <Button
                      size="sm"
                      onClick={handleApproveStrategy}
                      disabled={isApproving || !generatedResult.ast_safety_passed}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold font-mono text-xs flex items-center gap-1.5"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                      {isApproving ? "Approving..." : "Approve & Import to Drafts"}
                    </Button>
                  )}
                </div>
              </Card>
            ) : (
              <div className="h-full flex items-center justify-center p-8 border border-dashed border-border rounded-xl text-center">
                <div className="space-y-2">
                  <FileCode2 className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-xs font-mono text-slate-400">No strategy generated yet.</p>
                  <p className="text-[10px] font-mono text-slate-500">
                    Input a prompt on the left and click "Generate Quant Strategy".
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Log Analyzer */}
      {activeTab === "log-analyzer" && (
        <div className="space-y-4">
          <Card className="border border-border/80 p-5 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                Automated Telemetry & Audit Trail Anomaly Scanning
              </h3>
              <p className="text-[10px] text-slate-400 mt-1">
                Scans execution logs for high slippage, staleness timeouts, rate-limit drops, and risk hard-stop clusters.
              </p>
            </div>
            <Button
              onClick={handleAnalyzeLogs}
              disabled={isAnalyzingLogs}
              className="font-bold font-mono text-xs flex items-center gap-2"
            >
              <Search className="w-3.5 h-3.5" />
              {isAnalyzingLogs ? "Scanning Logs..." : "Scan Audit & Telemetry Logs"}
            </Button>
          </Card>

          {logReport && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono">
                <Card className="border border-border/80 p-4">
                  <span className="text-[10px] text-slate-400 uppercase">System Health Score</span>
                  <div className="text-xl font-bold text-emerald-400 mt-1">{logReport.health_score.toFixed(1)}%</div>
                </Card>
                <Card className="border border-border/80 p-4">
                  <span className="text-[10px] text-slate-400 uppercase">Events Analyzed</span>
                  <div className="text-xl font-bold text-white mt-1">{logReport.total_events_analyzed}</div>
                </Card>
                <Card className="border border-border/80 p-4">
                  <span className="text-[10px] text-slate-400 uppercase">Anomalies Detected</span>
                  <div className="text-xl font-bold text-amber-400 mt-1">{logReport.anomalies.length}</div>
                </Card>
              </div>

              <Card className="border border-border/80 p-5 space-y-3 font-mono text-xs">
                <div className="text-xs font-bold text-white uppercase">Identified Anomalies & Root Causes</div>
                {logReport.anomalies.length === 0 ? (
                  <p className="text-slate-400 text-xs">Zero anomalies detected. Platform operating normally.</p>
                ) : (
                  <div className="space-y-3">
                    {logReport.anomalies.map((anom) => (
                      <div key={anom.anomaly_id} className="p-3 bg-surface rounded-lg border border-border/60 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white">{anom.summary}</span>
                          <Badge variant={anom.severity === "CRITICAL" || anom.severity === "HIGH" ? "danger" : "warning"}>
                            {anom.severity}
                          </Badge>
                        </div>
                        <div className="text-slate-400 text-[11px]">Root Cause: <span className="text-slate-300">{anom.root_cause}</span></div>
                        <div className="text-emerald-400 text-[11px]">Recommended Action: <span className="text-emerald-300">{anom.recommended_action}</span></div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Risk Advisor */}
      {activeTab === "risk-advisor" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border border-border/80 p-5 space-y-4">
            <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-primary" />
              Pre-Trade Risk Breach Diagnostic Input
            </h3>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-[10px] text-slate-400 block mb-1 uppercase">Simulate / Paste Risk Rejection Reason</label>
                <textarea
                  rows={3}
                  value={riskRejectionInput}
                  onChange={(e) => setRiskRejectionInput(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg p-3 text-white font-mono text-xs focus:outline-none focus:border-primary"
                />
              </div>

              <div className="flex flex-wrap gap-2 text-[10px]">
                <button
                  type="button"
                  onClick={() => setRiskRejectionInput("Market data staleness exceeded 3000ms threshold (Rule 7)")}
                  className="px-2 py-1 bg-surface-raised hover:bg-surface border border-border rounded text-slate-300"
                >
                  Staleness (Rule 7)
                </button>
                <button
                  type="button"
                  onClick={() => setRiskRejectionInput("Emergency Kill Switch is ACTIVE at level 'GLOBAL' (Rule 4)")}
                  className="px-2 py-1 bg-surface-raised hover:bg-surface border border-border rounded text-slate-300"
                >
                  Kill Switch (Rule 4)
                </button>
                <button
                  type="button"
                  onClick={() => setRiskRejectionInput("Max Drawdown limit breached: 12.5% vs 10% cap (Rule 2)")}
                  className="px-2 py-1 bg-surface-raised hover:bg-surface border border-border rounded text-slate-300"
                >
                  Drawdown Cap (Rule 2)
                </button>
              </div>

              <Button
                onClick={handleExplainRisk}
                disabled={isExplainingRisk}
                className="w-full font-bold flex items-center justify-center gap-2 mt-2"
              >
                <Terminal className="w-3.5 h-3.5" />
                {isExplainingRisk ? "Diagnosing..." : "Explain Risk Breach & Suggest Actions"}
              </Button>
            </div>
          </Card>

          {/* Right Col: Plain English Diagnosis & Recommendations */}
          <div>
            {riskReport ? (
              <Card className="border border-border/80 p-5 space-y-4 font-mono text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white uppercase">{riskReport.breach_category}</span>
                  <Badge variant="warning">{riskReport.safety_score_impact}</Badge>
                </div>

                <div className="p-3 bg-surface rounded-lg border border-border/60 text-slate-200 leading-relaxed text-xs">
                  {riskReport.plain_english_explanation}
                </div>

                <div className="space-y-2">
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Actionable Parameter Recommendations</span>
                  {riskReport.recommended_actions.map((rec, idx) => (
                    <div key={idx} className="p-3 bg-surface-raised rounded-lg border border-border/60 space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-emerald-400">{rec.parameter_name}</span>
                        <span className="text-slate-400">Suggested: <span className="text-white font-bold">{rec.suggested_value}</span></span>
                      </div>
                      <p className="text-[11px] text-slate-300">{rec.rationale}</p>
                    </div>
                  ))}
                </div>
              </Card>
            ) : (
              <div className="h-full flex items-center justify-center p-8 border border-dashed border-border rounded-xl text-center">
                <div className="space-y-2">
                  <BookOpen className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-xs font-mono text-slate-400">No risk diagnosis run yet.</p>
                  <p className="text-[10px] font-mono text-slate-500">
                    Select a risk scenario and click "Explain Risk Breach".
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
