import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { OrderManagementPage } from "./OrderManagementPage";

describe("OrderManagementPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    }));
  });

  it("renders order ticket form, positions, and order lifecycle tables", () => {
    render(<OrderManagementPage />);

    expect(screen.getByText("Order Management System & Position Engine")).toBeDefined();
    expect(screen.getByText("Direct Order Ticket")).toBeDefined();
    expect(screen.getByText("Live Portfolio Positions")).toBeDefined();
    expect(screen.getByText("OMS Order Execution Log & Lifecycle States")).toBeDefined();
  });

  it("allows submitting an order from the ticket form", async () => {
    render(<OrderManagementPage />);

    const submitBtn = screen.getByRole("button", { name: /Dispatch BUY 10 AAPL/i });
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    expect(screen.getAllByText("AAPL").length).toBeGreaterThan(0);
  });
});
