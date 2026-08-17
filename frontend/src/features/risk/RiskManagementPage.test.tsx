import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { RiskManagementPage } from "./RiskManagementPage";

describe("RiskManagementPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((url: string) => {
      if (url.includes("/evaluate-pre-trade")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            allowed: true,
            rejection_reasons: [],
            checks: [
              {
                check_type: "KILL_SWITCH",
                passed: true,
                severity: "BLOCKING",
                rule_name: "Emergency Kill Switch Guard",
                message: "Kill switch inactive. Execution allowed.",
                details: {},
              },
            ],
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          max_daily_loss_percent: 3.0,
          max_drawdown_percent: 5.0,
          max_position_size_percent: 10.0,
          max_orders_per_second: 10,
          max_open_orders_per_symbol: 10,
          self_trade_prevention: true,
          kill_switch: {
            is_active: false,
            level: "GLOBAL",
            positions_flattened: false,
          },
        }),
      });
    }));
  });

  it("renders Risk Engine header, Emergency Kill Switch, and parameters form", () => {
    render(<RiskManagementPage />);

    expect(screen.getByText("Synchronous Pre-Trade Risk Engine & Emergency Controls")).toBeDefined();
    expect(screen.getByText("1-Click Global Emergency Kill Switch")).toBeDefined();
    expect(screen.getByText("Pre-Trade Hard-Stop Parameters")).toBeDefined();
    expect(screen.getByText("Pre-Trade Risk Engine Dry-Run Simulator")).toBeDefined();
  });

  it("allows triggering pre-trade risk evaluation dry run", async () => {
    render(<RiskManagementPage />);

    const evalBtn = screen.getByRole("button", { name: /Evaluate Order Pre-Trade/i });
    await act(async () => {
      fireEvent.click(evalBtn);
    });

    expect(screen.getByText("PRE-TRADE CHECKS PASSED")).toBeDefined();
    expect(screen.getByText("Emergency Kill Switch Guard")).toBeDefined();
  });
});
