import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { AIAdvisorySuitePage } from "./AIAdvisorySuitePage";

describe("AIAdvisorySuitePage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: any) => {
      const url = typeof input === "string" ? input : input?.url || "";

      if (url.includes("/ai/generate-strategy")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            generation_id: "gen_test_01",
            strategy_name: "AI_Dual_EMA_Strategy",
            code: "class AI_Dual_EMA_Strategy(BaseStrategy): pass",
            description: "Generated strategy for testing",
            parameters: [],
            ast_safety_passed: true,
            ast_violations: [],
            review_status: "PENDING_HUMAN_REVIEW",
            advisory_disclaimer: "Rule 3 Advisory Only",
            generated_at: new Date().toISOString(),
          }),
        });
      }

      if (url.includes("/ai/approve/")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            generation_id: "gen_test_01",
            strategy_name: "AI_Dual_EMA_Strategy",
            code: "class AI_Dual_EMA_Strategy(BaseStrategy): pass",
            description: "Generated strategy for testing",
            parameters: [],
            ast_safety_passed: true,
            ast_violations: [],
            review_status: "APPROVED_BY_HUMAN",
            reviewed_by: "human_tester",
            reviewed_at: new Date().toISOString(),
            advisory_disclaimer: "Rule 3 Advisory Only",
            generated_at: new Date().toISOString(),
          }),
        });
      }

      if (url.includes("/ai/analyze-logs")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            report_id: "rep_log_1",
            total_events_analyzed: 45,
            health_score: 98.0,
            anomalies: [],
            summary: "Platform operating stably.",
            generated_at: new Date().toISOString(),
          }),
        });
      }

      if (url.includes("/ai/explain-risk")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            report_id: "rep_risk_1",
            plain_english_explanation: "Order rejected due to Rule 7 staleness check.",
            breach_category: "MARKET_DATA_STALENESS",
            recommended_actions: [
              {
                parameter_name: "feed_interval",
                current_value: "5000ms",
                suggested_value: "1000ms",
                rationale: "Reconnect socket",
              },
            ],
            safety_score_impact: "Neutral",
            generated_at: new Date().toISOString(),
          }),
        });
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({ status: "success" }),
      });
    }));
  });

  it("renders AI advisory suite and generates strategy", async () => {
    render(<AIAdvisorySuitePage />);

    expect(screen.getByText("AI Advisory Suite")).toBeDefined();
    expect(screen.getByText(/Non-Negotiable Rule 3: AI Output is Advisory Only/i)).toBeDefined();

    const genBtn = screen.getByRole("button", { name: /Generate Quant Strategy/i });
    await act(async () => {
      fireEvent.click(genBtn);
    });

    await waitFor(() => {
      expect(screen.getByText(/AST: PASSED/i)).toBeDefined();
      expect(screen.getByText("PENDING_HUMAN_REVIEW")).toBeDefined();
    });
  });

  it("approves strategy code and marks approved by human", async () => {
    render(<AIAdvisorySuitePage />);

    const genBtn = screen.getByRole("button", { name: /Generate Quant Strategy/i });
    await act(async () => {
      fireEvent.click(genBtn);
    });

    await waitFor(() => {
      expect(screen.getByText(/Approve & Import to Drafts/i)).toBeDefined();
    });

    const apprBtn = screen.getByRole("button", { name: /Approve & Import to Drafts/i });
    await act(async () => {
      fireEvent.click(apprBtn);
    });

    await waitFor(() => {
      expect(screen.getByText("APPROVED_BY_HUMAN")).toBeDefined();
    });
  });

  it("switches to log analyzer and scans logs", async () => {
    render(<AIAdvisorySuitePage />);

    const logTab = screen.getByText("Log & Telemetry Analyzer");
    await act(async () => {
      fireEvent.click(logTab);
    });

    const scanBtn = screen.getByRole("button", { name: /Scan Audit & Telemetry Logs/i });
    await act(async () => {
      fireEvent.click(scanBtn);
    });

    await waitFor(() => {
      expect(screen.getByText("98.0%")).toBeDefined();
    });
  });
});
