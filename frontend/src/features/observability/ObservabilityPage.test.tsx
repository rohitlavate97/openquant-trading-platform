import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { ObservabilityPage } from "./ObservabilityPage";

describe("ObservabilityPage", () => {
  it("renders observability console header and metrics overview", () => {
    render(<ObservabilityPage />);
    expect(screen.getByText("Observability & Monitoring")).toBeDefined();
    expect(screen.getByText("Prometheus • OpenTelemetry • Grafana")).toBeDefined();
    expect(screen.getByText("Total HTTP API Requests")).toBeDefined();
    expect(screen.getByText("Risk Checks Evaluated")).toBeDefined();
    expect(screen.getByText("Market Ticks Ingested")).toBeDefined();
  });

  it("switches to distributed traces and grafana dashboards tabs", async () => {
    render(<ObservabilityPage />);

    // Switch to Distributed Traces
    await act(async () => {
      fireEvent.click(screen.getByText("Distributed Traces"));
    });
    expect(screen.getByPlaceholderText("Search by Trace ID or Span name...")).toBeDefined();

    // Switch to Prometheus Exporter
    await act(async () => {
      fireEvent.click(screen.getByText("Prometheus Exporter"));
    });
    expect(screen.getByText("Prometheus OpenMetrics Live Text Exposition")).toBeDefined();

    // Switch to Grafana Dashboards
    await act(async () => {
      fireEvent.click(screen.getByText("Grafana Dashboards"));
    });
    expect(screen.getByText("OpenQuant - Trading Operations & OMS")).toBeDefined();
    expect(screen.getByText("OpenQuant - Pre-Trade Risk & Kill Switch")).toBeDefined();
  });
});
