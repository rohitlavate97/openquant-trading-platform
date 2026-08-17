import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { LiveTradingConsolePage } from "./LiveTradingConsolePage";

describe("LiveTradingConsolePage", () => {
  it("renders live trading console header and mission control summary", () => {
    render(<LiveTradingConsolePage />);
    expect(screen.getByText("Live Trading Mission Control")).toBeDefined();
    expect(screen.getByText("Stage 4 Execution Gated")).toBeDefined();
    expect(screen.getByText("Live Deployment Launch Pad")).toBeDefined();
  });

  it("calculates effective capital scaling when tier is selected", async () => {
    render(<LiveTradingConsolePage />);

    // Click Intermediate (50%)
    await act(async () => {
      fireEvent.click(screen.getByText("Intermediate"));
    });
    expect(screen.getByText("50% Size")).toBeDefined();

    // Click Full (100%)
    await act(async () => {
      fireEvent.click(screen.getByText("Full Scaling"));
    });
    expect(screen.getByText("100% Size")).toBeDefined();
  });

  it("handles emergency halt on active live session", async () => {
    vi.spyOn(window, "confirm").mockImplementation(() => true);
    render(<LiveTradingConsolePage />);

    const haltBtn = screen.getByText("Emergency Halt");
    expect(haltBtn).toBeDefined();

    await act(async () => {
      fireEvent.click(haltBtn);
    });
    expect(screen.getByText(/EMERGENCY HALTED/i)).toBeDefined();
  });
});
