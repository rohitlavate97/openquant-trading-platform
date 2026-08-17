import React, { useState } from "react";
import {
  LivePreflightReport,
  LiveStrategySession,
  ScalingTier,
} from "../../types/liveTrading";

export const LiveTradingConsolePage: React.FC = () => {
  const [sessions, setSessions] = useState<LiveStrategySession[]>([
    {
      session_id: "live_a982f1b4c0",
      strategy_id: "strat_prod_alpha",
      strategy_name: "Multi-Asset Momentum Alpha",
      broker_id: "interactive_brokers",
      account_id: "U9876543",
      allocation: {
        strategy_id: "strat_prod_alpha",
        broker_id: "interactive_brokers",
        account_id: "U9876543",
        total_authorized_capital: "100000.00",
        scaling_tier: "TIER_1_STARTER",
        max_order_notional: "10000.00",
        margin_floor_buffer: "15000.00",
        max_daily_loss: "3000.00",
        max_drawdown_percent: "5.00",
        effective_allocated_capital: "25000.00",
      },
      state: "ACTIVE",
      activated_by: "quant_officer",
      confirmed_by: "risk_director",
      activated_at: new Date(Date.now() - 3600000 * 4).toISOString(),
      realized_pnl: "+1450.00",
      unrealized_pnl: "+820.50",
      live_orders_count: 14,
    },
  ]);

  const [selectedStrategy, setSelectedStrategy] = useState("strat_prod_alpha");
  const [selectedBroker, setSelectedBroker] = useState("interactive_brokers");
  const [accountId, setAccountId] = useState("U9876543");
  const [authorizedCapital, setAuthorizedCapital] = useState("100000.00");
  const [scalingTier, setScalingTier] = useState<ScalingTier>("TIER_1_STARTER");
  const [maxOrderNotional, setMaxOrderNotional] = useState("10000.00");
  const [marginBuffer, setMarginBuffer] = useState("15000.00");
  const [maxDailyLoss, setMaxDailyLoss] = useState("3000.00");
  const [maxDrawdown, setMaxDrawdown] = useState("5.00");

  const [preflightReport, setPreflightReport] = useState<LivePreflightReport | null>(null);
  const [isCheckingPreflight, setIsCheckingPreflight] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmedByInput, setConfirmedByInput] = useState("risk_officer_primary");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Scaling multiplier calculation
  const getMultiplier = (tier: ScalingTier): number => {
    switch (tier) {
      case "TIER_1_STARTER":
        return 0.25;
      case "TIER_2_INTERMEDIATE":
        return 0.5;
      case "TIER_3_FULL":
        return 1.0;
    }
  };

  const effectiveCapital = (parseFloat(authorizedCapital || "0") * getMultiplier(scalingTier)).toFixed(2);

  const handleRunPreflight = () => {
    setIsCheckingPreflight(true);
    setStatusMessage(null);

    // Simulate API preflight evaluation
    setTimeout(() => {
      setPreflightReport({
        strategy_id: selectedStrategy,
        broker_id: selectedBroker,
        account_id: accountId,
        is_eligible: true,
        checked_at: new Date().toISOString(),
        checks: [
          {
            check_name: "PROMOTION_GATE_STAGE_4",
            passed: true,
            description: "Verified strategy is approved in Stage 4 (LIVE_TRADING).",
            is_blocking: true,
          },
          {
            check_name: "CERTIFIED_BROKER_ADAPTER",
            passed: true,
            description: `Broker adapter '${selectedBroker}' certified via automated 5-point sandbox audit.`,
            is_blocking: true,
          },
          {
            check_name: "PRE_TRADE_RISK_ENGINE_UNBLOCKED",
            passed: true,
            description: "Risk Engine is active and Global Kill Switch is UNLOCKED.",
            is_blocking: true,
          },
          {
            check_name: "MARKET_DATA_STALENESS_GUARD",
            passed: true,
            description: "All market data latency feeds are HEALTHY (< 3000ms staleness threshold).",
            is_blocking: true,
          },
          {
            check_name: "BROKER_AUTHENTICATED_SESSION",
            passed: true,
            description: `Active authenticated session verified with '${selectedBroker}'.`,
            is_blocking: true,
          },
        ],
        rejection_reasons: [],
      });
      setIsCheckingPreflight(false);
      setStatusMessage("Preflight readiness checks passed! All non-negotiable prerequisites satisfied.");
    }, 600);
  };

  const handleActivateSession = () => {
    if (!preflightReport || !preflightReport.is_eligible) {
      alert("Please run and pass all preflight readiness checks before activating live trading.");
      return;
    }
    setShowConfirmModal(true);
  };

  const confirmActivation = () => {
    const newSession: LiveStrategySession = {
      session_id: `live_${Math.random().toString(36).substring(2, 10)}`,
      strategy_id: selectedStrategy,
      strategy_name: selectedStrategy === "strat_prod_alpha" ? "Multi-Asset Momentum Alpha" : "Crypto Grid Arbitrage",
      broker_id: selectedBroker,
      account_id: accountId,
      allocation: {
        strategy_id: selectedStrategy,
        broker_id: selectedBroker,
        account_id: accountId,
        total_authorized_capital: authorizedCapital,
        scaling_tier: scalingTier,
        max_order_notional: maxOrderNotional,
        margin_floor_buffer: marginBuffer,
        max_daily_loss: maxDailyLoss,
        max_drawdown_percent: maxDrawdown,
        effective_allocated_capital: effectiveCapital,
      },
      state: "ACTIVE",
      activated_by: "system_admin",
      confirmed_by: confirmedByInput,
      activated_at: new Date().toISOString(),
      realized_pnl: "0.00",
      unrealized_pnl: "0.00",
      live_orders_count: 0,
      preflight_report: preflightReport || undefined,
    };

    setSessions([newSession, ...sessions]);
    setShowConfirmModal(false);
    setStatusMessage(`Live Session '${newSession.session_id}' ACTIVATED with ${effectiveCapital} capital allocation.`);
  };

  const handleScaleSession = (sessionId: string, newTier: ScalingTier) => {
    setSessions(
      sessions.map((s) => {
        if (s.session_id === sessionId) {
          const auth = parseFloat(s.allocation.total_authorized_capital);
          const effective = (auth * getMultiplier(newTier)).toFixed(2);
          return {
            ...s,
            allocation: {
              ...s.allocation,
              scaling_tier: newTier,
              effective_allocated_capital: effective,
            },
          };
        }
        return s;
      })
    );
    setStatusMessage(`Session '${sessionId}' scaled to ${newTier}.`);
  };

  const handleHaltSession = (sessionId: string) => {
    if (window.confirm(`Are you sure you want to EMERGENCY HALT live session '${sessionId}'?`)) {
      setSessions(
        sessions.map((s) =>
          s.session_id === sessionId
            ? { ...s, state: "HALTED", halt_reason: "Manual operator emergency halt", deactivated_at: new Date().toISOString() }
            : s
        )
      );
      setStatusMessage(`Session '${sessionId}' EMERGENCY HALTED.`);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <h1 className="text-3xl font-bold tracking-tight text-text">Live Trading Mission Control</h1>
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Stage 4 Execution Gated
            </span>
          </div>
          <p className="text-text-muted mt-2 text-sm">
            Orchestrate production strategy execution with automated 5-point preflight verification, gradual position scaling, and risk hard stops.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="bg-surface-elevated px-4 py-2 rounded-lg border border-border">
            <div className="text-xs text-text-muted">Active Sessions</div>
            <div className="text-xl font-bold text-text">{sessions.filter((s) => s.state === "ACTIVE").length}</div>
          </div>
          <div className="bg-surface-elevated px-4 py-2 rounded-lg border border-border">
            <div className="text-xs text-text-muted">Live Allocated Capital</div>
            <div className="text-xl font-bold text-emerald-400">
              $
              {sessions
                .filter((s) => s.state === "ACTIVE")
                .reduce((acc, s) => acc + parseFloat(s.allocation.effective_allocated_capital || "0"), 0)
                .toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {statusMessage && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-center justify-between">
          <span>{statusMessage}</span>
          <button onClick={() => setStatusMessage(null)} className="text-emerald-400 hover:text-emerald-200 text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Grid: Launch Pad & Active Sessions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Preflight & Launch Pad */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-surface rounded-xl border border-border p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Live Deployment Launch Pad
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Select Stage 4 Strategy</label>
                <select
                  aria-label="Select Stage 4 Strategy"
                  value={selectedStrategy}
                  onChange={(e) => setSelectedStrategy(e.target.value)}
                  className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-sm text-text focus:outline-none focus:border-indigo-500"
                >
                  <option value="strat_prod_alpha">Multi-Asset Momentum Alpha (Stage 4 LIVE)</option>
                  <option value="strat_crypto_grid">Crypto Grid Arbitrage (Stage 4 LIVE)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Target Broker Adapter</label>
                  <select
                    aria-label="Target Broker Adapter"
                    value={selectedBroker}
                    onChange={(e) => setSelectedBroker(e.target.value)}
                    className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-sm text-text focus:outline-none focus:border-indigo-500"
                  >
                    <option value="interactive_brokers">Interactive Brokers</option>
                    <option value="binance_crypto">Binance Crypto</option>
                    <option value="zerodha">Zerodha Kite</option>
                    <option value="angelone">Angel One SmartAPI</option>
                    <option value="paper_broker">Paper Sandbox Broker</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Broker Account ID</label>
                  <input
                    type="text"
                    value={accountId}
                    onChange={(e) => setAccountId(e.target.value)}
                    className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-sm text-text focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Capital Allocation & Scaling */}
              <div className="border-t border-border pt-4 space-y-4">
                <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider">Capital & Scaling Parameters</h3>

                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Total Authorized Capital ($)</label>
                  <input
                    type="number"
                    value={authorizedCapital}
                    onChange={(e) => setAuthorizedCapital(e.target.value)}
                    className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-sm text-text focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-text-muted mb-2">Gradual Position Scaling Tier</label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      type="button"
                      onClick={() => setScalingTier("TIER_1_STARTER")}
                      className={`px-3 py-2 text-xs font-medium rounded-lg border text-center transition-all ${
                        scalingTier === "TIER_1_STARTER"
                          ? "bg-indigo-600/20 border-indigo-500 text-indigo-300 font-bold"
                          : "bg-surface-elevated border-border text-text-muted hover:border-text-muted"
                      }`}
                    >
                      <div>Starter</div>
                      <div className="text-[10px] text-indigo-400">25% Size</div>
                    </button>
                    <button
                      type="button"
                      onClick={() => setScalingTier("TIER_2_INTERMEDIATE")}
                      className={`px-3 py-2 text-xs font-medium rounded-lg border text-center transition-all ${
                        scalingTier === "TIER_2_INTERMEDIATE"
                          ? "bg-indigo-600/20 border-indigo-500 text-indigo-300 font-bold"
                          : "bg-surface-elevated border-border text-text-muted hover:border-text-muted"
                      }`}
                    >
                      <div>Intermediate</div>
                      <div className="text-[10px] text-indigo-400">50% Size</div>
                    </button>
                    <button
                      type="button"
                      onClick={() => setScalingTier("TIER_3_FULL")}
                      className={`px-3 py-2 text-xs font-medium rounded-lg border text-center transition-all ${
                        scalingTier === "TIER_3_FULL"
                          ? "bg-indigo-600/20 border-indigo-500 text-indigo-300 font-bold"
                          : "bg-surface-elevated border-border text-text-muted hover:border-text-muted"
                      }`}
                    >
                      <div>Full Scaling</div>
                      <div className="text-[10px] text-indigo-400">100% Size</div>
                    </button>
                  </div>
                </div>

                {/* Effective Capital Sizing Banner */}
                <div className="p-3 bg-surface-elevated rounded-lg border border-border flex items-center justify-between text-xs">
                  <span className="text-text-muted">Effective Live Allocated Capital:</span>
                  <span className="text-sm font-bold text-emerald-400">${parseFloat(effectiveCapital).toLocaleString()}</span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="block text-text-muted mb-1">Max Order Notional ($)</label>
                    <input
                      type="number"
                      value={maxOrderNotional}
                      onChange={(e) => setMaxOrderNotional(e.target.value)}
                      className="w-full bg-surface-elevated border border-border rounded-lg px-2.5 py-1.5 text-text text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-text-muted mb-1">Margin Floor Buffer ($)</label>
                    <input
                      type="number"
                      value={marginBuffer}
                      onChange={(e) => setMarginBuffer(e.target.value)}
                      className="w-full bg-surface-elevated border border-border rounded-lg px-2.5 py-1.5 text-text text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-text-muted mb-1">Max Daily Loss ($)</label>
                    <input
                      type="number"
                      value={maxDailyLoss}
                      onChange={(e) => setMaxDailyLoss(e.target.value)}
                      className="w-full bg-surface-elevated border border-border rounded-lg px-2.5 py-1.5 text-text text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-text-muted mb-1">Max Peak Drawdown (%)</label>
                    <input
                      type="number"
                      value={maxDrawdown}
                      onChange={(e) => setMaxDrawdown(e.target.value)}
                      className="w-full bg-surface-elevated border border-border rounded-lg px-2.5 py-1.5 text-text text-xs"
                    />
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 space-y-2">
                <button
                  type="button"
                  onClick={handleRunPreflight}
                  disabled={isCheckingPreflight}
                  className="w-full py-2.5 px-4 rounded-lg bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-sm font-medium text-text flex items-center justify-center gap-2 transition-all"
                >
                  {isCheckingPreflight ? (
                    <span>Verifying 5-Point Prerequisites...</span>
                  ) : (
                    <>
                      <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>Run Preflight Readiness Check</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleActivateSession}
                  disabled={!preflightReport || !preflightReport.is_eligible}
                  className={`w-full py-2.5 px-4 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all ${
                    preflightReport && preflightReport.is_eligible
                      ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20"
                      : "bg-surface-elevated text-text-muted opacity-50 cursor-not-allowed border border-border"
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Authorize & Activate Live Trading</span>
                </button>
              </div>
            </div>
          </div>

          {/* Preflight Checklist Card */}
          {preflightReport && (
            <div className="bg-surface rounded-xl border border-border p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-text">Preflight Verification Matrix</h3>
                <span
                  className={`px-2 py-0.5 text-xs font-semibold rounded ${
                    preflightReport.is_eligible ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"
                  }`}
                >
                  {preflightReport.is_eligible ? "ELIGIBLE FOR LIVE" : "BLOCKED"}
                </span>
              </div>

              <div className="space-y-3">
                {preflightReport.checks.map((c, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-2.5 rounded-lg bg-surface-elevated border border-border/50 text-xs">
                    <span className={`p-1 rounded-full ${c.passed ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"}`}>
                      {c.passed ? (
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )}
                    </span>
                    <div className="flex-1">
                      <div className="font-semibold text-text">{c.check_name}</div>
                      <div className="text-text-muted text-[11px] mt-0.5">{c.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Active Live Strategy Sessions */}
        <div className="lg:col-span-7 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-text">Active Live Strategy Sessions</h2>
            <span className="text-xs text-text-muted">{sessions.length} Deployments Recorded</span>
          </div>

          <div className="space-y-4">
            {sessions.map((session) => (
              <div key={session.session_id} className="bg-surface rounded-xl border border-border p-6 shadow-sm space-y-5">
                {/* Session Header */}
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2.5 py-0.5 text-xs font-bold rounded-full ${
                          session.state === "ACTIVE"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : session.state === "HALTED"
                            ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                            : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                        }`}
                      >
                        {session.state}
                      </span>
                      <h3 className="text-base font-bold text-text">{session.strategy_name}</h3>
                    </div>
                    <div className="text-xs text-text-muted mt-1 flex items-center gap-3">
                      <span>ID: {session.session_id}</span>
                      <span>•</span>
                      <span>Broker: {session.broker_id}</span>
                      <span>•</span>
                      <span>Account: {session.account_id}</span>
                    </div>
                  </div>

                  {/* 1-Click Emergency Stop */}
                  {session.state === "ACTIVE" && (
                    <button
                      type="button"
                      onClick={() => handleHaltSession(session.session_id)}
                      className="px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/40 text-rose-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                      </svg>
                      <span>Emergency Halt</span>
                    </button>
                  )}
                </div>

                {/* Session Key Telemetry */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="bg-surface-elevated p-3 rounded-lg border border-border">
                    <div className="text-[11px] text-text-muted">Effective Capital</div>
                    <div className="text-sm font-bold text-emerald-400">
                      ${parseFloat(session.allocation.effective_allocated_capital || "0").toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-surface-elevated p-3 rounded-lg border border-border">
                    <div className="text-[11px] text-text-muted">Realized PnL</div>
                    <div className="text-sm font-bold text-emerald-400">{session.realized_pnl}</div>
                  </div>
                  <div className="bg-surface-elevated p-3 rounded-lg border border-border">
                    <div className="text-[11px] text-text-muted">Unrealized PnL</div>
                    <div className="text-sm font-bold text-emerald-400">{session.unrealized_pnl}</div>
                  </div>
                  <div className="bg-surface-elevated p-3 rounded-lg border border-border">
                    <div className="text-[11px] text-text-muted">Live Orders</div>
                    <div className="text-sm font-bold text-text">{session.live_orders_count} Filled</div>
                  </div>
                </div>

                {/* Quick Scaling Controls */}
                {session.state === "ACTIVE" && (
                  <div className="flex items-center justify-between border-t border-border pt-3 text-xs">
                    <span className="text-text-muted">Scaling Tier:</span>
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => handleScaleSession(session.session_id, "TIER_1_STARTER")}
                        className={`px-2.5 py-1 rounded text-[11px] font-medium border transition-all ${
                          session.allocation.scaling_tier === "TIER_1_STARTER"
                            ? "bg-indigo-600 text-white border-indigo-500"
                            : "bg-surface-elevated text-text-muted border-border hover:text-text"
                        }`}
                      >
                        Starter (25%)
                      </button>
                      <button
                        type="button"
                        onClick={() => handleScaleSession(session.session_id, "TIER_2_INTERMEDIATE")}
                        className={`px-2.5 py-1 rounded text-[11px] font-medium border transition-all ${
                          session.allocation.scaling_tier === "TIER_2_INTERMEDIATE"
                            ? "bg-indigo-600 text-white border-indigo-500"
                            : "bg-surface-elevated text-text-muted border-border hover:text-text"
                        }`}
                      >
                        Intermediate (50%)
                      </button>
                      <button
                        type="button"
                        onClick={() => handleScaleSession(session.session_id, "TIER_3_FULL")}
                        className={`px-2.5 py-1 rounded text-[11px] font-medium border transition-all ${
                          session.allocation.scaling_tier === "TIER_3_FULL"
                            ? "bg-indigo-600 text-white border-indigo-500"
                            : "bg-surface-elevated text-text-muted border-border hover:text-text"
                        }`}
                      >
                        Full (100%)
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Dual Confirmation Verification Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-surface border border-border rounded-xl max-w-md w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center gap-3 text-amber-400">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h3 className="text-lg font-bold text-text">Dual-Operator Authorization</h3>
            </div>

            <p className="text-xs text-text-muted">
              Live trading initiates real-money order routing to connected exchange endpoints. Non-Negotiable Rule 1 requires secondary confirmation from a certified risk officer.
            </p>

            <div className="bg-surface-elevated p-3 rounded-lg border border-border space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-text-muted">Strategy:</span>
                <span className="font-semibold text-text">{selectedStrategy}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Broker:</span>
                <span className="font-semibold text-text">{selectedBroker}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Effective Capital:</span>
                <span className="font-bold text-emerald-400">${parseFloat(effectiveCapital).toLocaleString()}</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">Secondary Approver / Risk Officer ID</label>
              <input
                type="text"
                value={confirmedByInput}
                onChange={(e) => setConfirmedByInput(e.target.value)}
                className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-sm text-text focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                className="px-4 py-2 bg-surface-elevated border border-border rounded-lg text-xs font-medium text-text hover:bg-surface-elevated/80"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmActivation}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-emerald-600/20"
              >
                Confirm & Launch Live Strategy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveTradingConsolePage;
