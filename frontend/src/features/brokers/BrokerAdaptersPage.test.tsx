import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { BrokerAdaptersPage } from "./BrokerAdaptersPage";

describe("BrokerAdaptersPage", () => {
  it("renders registered broker adapters and funds metrics", () => {
    render(<BrokerAdaptersPage />);

    expect(screen.getByText("Broker Adapter Interface & Certification")).toBeDefined();
    expect(screen.getByText("OpenQuant Paper Engine")).toBeDefined();
    expect(screen.getByText("Zerodha Kite Connect")).toBeDefined();
    expect(screen.getAllByText("Total Balance").length).toBeGreaterThan(0);
  });

  it("allows selecting an adapter and triggering audit harness", async () => {
    render(<BrokerAdaptersPage />);

    const auditButtons = screen.getAllByRole("button", { name: /Audit Harness/i });
    expect(auditButtons.length).toBeGreaterThan(0);
    await act(async () => {
      fireEvent.click(auditButtons[0]);
    });
  });
});
