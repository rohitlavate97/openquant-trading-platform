import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { AuditLogViewer } from "./AuditLogViewer";

describe("AuditLogViewer", () => {
  it("renders audit log table and entries", () => {
    render(<AuditLogViewer />);

    expect(screen.getByText("Immutable Audit Trail & Compliance Logs")).toBeDefined();
    expect(screen.getByText("KILL_SWITCH_STATUS")).toBeDefined();
    expect(screen.getAllByText("CRITICAL").length).toBeGreaterThan(0);
    expect(screen.getByText("BROKER_CREDENTIALS_STORED")).toBeDefined();
  });

  it("filters logs by severity", () => {
    render(<AuditLogViewer />);

    const critBtn = screen.getByRole("button", { name: "CRITICAL" });
    fireEvent.click(critBtn);

    expect(screen.getByText("KILL_SWITCH_STATUS")).toBeDefined();
  });
});
