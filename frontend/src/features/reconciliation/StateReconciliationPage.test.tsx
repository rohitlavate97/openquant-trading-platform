import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { StateReconciliationPage } from "./StateReconciliationPage";

describe("StateReconciliationPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: any) => {
      const url = typeof input === "string" ? input : input?.url || "";

      if (url.includes("/reports")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            {
              report_id: "recon_demo_1",
              account_id: "acc_main",
              broker_id: "paper_broker",
              status: "CLEAN",
              position_discrepancies: [],
              order_discrepancies: [],
              auto_halt_triggered: false,
              reconciled_at: new Date().toISOString(),
            },
          ],
        });
      }

      if (url.includes("/run")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            {
              report_id: "recon_demo_2",
              account_id: "acc_main",
              broker_id: "paper_broker",
              status: "CLEAN",
              position_discrepancies: [],
              order_discrepancies: [],
              auto_halt_triggered: false,
              reconciled_at: new Date().toISOString(),
            },
          ],
        });
      }

      if (url.includes("/sync")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            report_id: "recon_sync_1",
            account_id: "acc_main",
            broker_id: "paper_broker",
            status: "CLEAN",
            position_discrepancies: [],
            order_discrepancies: [],
            auto_halt_triggered: false,
            reconciled_at: new Date().toISOString(),
          }),
        });
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({ status: "success" }),
      });
    }));
  });

  it("renders state reconciliation page and overview metrics", async () => {
    render(<StateReconciliationPage />);

    expect(screen.getByText("State Reconciliation Engine (Rule 5 Mismatch Guard)")).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("Clean Reconciliations")).toBeDefined();
      expect(screen.getByText("Discrepancy Halts")).toBeDefined();
      expect(screen.getByText("Rule 5 Guard Interlock")).toBeDefined();
    });

    expect(screen.getByRole("button", { name: /Run Global Reconcile/i })).toBeDefined();
    expect(screen.getByRole("button", { name: /Force Sync with Broker/i })).toBeDefined();
  });

  it("triggers global reconciliation on clicking Run Global Reconcile", async () => {
    render(<StateReconciliationPage />);

    const runBtn = screen.getByRole("button", { name: /Run Global Reconcile/i });
    await act(async () => {
      fireEvent.click(runBtn);
    });

    await waitFor(() => {
      expect(screen.getByText(/Global state reconciliation completed/i)).toBeDefined();
    });
  });
});
