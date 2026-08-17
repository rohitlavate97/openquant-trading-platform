import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { StrategyManagementPage } from "./StrategyManagementPage";

describe("StrategyManagementPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [
        {
          strategy_id: "strat_momentum_1",
          name: "Alpha EMA Trend",
          description: "Dual EMA Crossover strategy",
          author_id: "usr_quant_1",
          source_code: "# EMAMomentumStrategy\nfast_sma = 0\n",
          parameters: [
            { name: "fast_period", param_type: "INT", default_value: 3, current_value: 3 },
            { name: "slow_period", param_type: "INT", default_value: 5, current_value: 5 },
          ],
          promotion_stage: "PAPER",
          state: "RUNNING",
          symbols: ["AAPL", "MSFT"],
          timeframes: ["1m"],
          account_id: "acc_main",
          broker_id: "paper_broker",
          total_trades: 20,
          winning_trades: 13,
          total_pnl: 2450.0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    }));
  });

  it("renders Strategy Execution Engine title and strategy cards", () => {
    render(<StrategyManagementPage />);

    expect(screen.getByText("Strategy Execution Engine")).toBeDefined();
    expect(screen.getByText("Active Strategies (0)")).toBeDefined();
  });

  it("opens create strategy modal upon clicking New Strategy", async () => {
    render(<StrategyManagementPage />);

    const newBtn = screen.getByRole("button", { name: /New Strategy/i });
    await act(async () => {
      fireEvent.click(newBtn);
    });

    expect(screen.getByText("Deploy Quantitative Strategy")).toBeDefined();
    expect(screen.getByText("Validate & Deploy Strategy")).toBeDefined();
  });
});
