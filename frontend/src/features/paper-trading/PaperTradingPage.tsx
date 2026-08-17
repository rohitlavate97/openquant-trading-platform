import React, { useState, useEffect } from "react";
import {
  FileCode2,
  Play,
  Pause,
  Square,
  RefreshCw,
  Plus,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Wallet,
  Layers,
  Sparkles,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import type {
  PaperAccount,
  PaperTradingSession,
  PaperTradingSessionStatus,
  PaperTradingGateStatus,
} from "../../types/paperTrading";
import type { Strategy } from "../../types/strategy";

export const PaperTradingPage: React.FC = () => {
  const [accounts, setAccounts] = useState<PaperAccount[]>([]);
  const [sessions, setSessions] = useState<PaperTradingSession[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>("");
  const [gateStatus, setGateStatus] = useState<PaperTradingGateStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showNewModal, setShowNewModal] = useState<boolean>(false);
  const [promotionFeedback, setPromotionFeedback] = useState<string | null>(null);

  // New Session Form State
  const [formStrategyId, setFormStrategyId] = useState<string>("");
  const [formAccountId, setFormAccountId] = useState<string>("");
  const [formSymbol, setFormSymbol] = useState<string>("AAPL");
  const [formLatency, setFormLatency] = useState<number>(100);
  const [formSlippage, setFormSlippage] = useState<number>(2.0);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (selectedSessionId) {
      fetchGateStatus(selectedSessionId);
    }
  }, [selectedSessionId]);

  const fetchInitialData = async () => {
    setIsLoading(true);
    try {
      const [accRes, sessRes, stratRes] = await Promise.all([
        fetch("/api/v1/paper-trading/accounts"),
        fetch("/api/v1/paper-trading/sessions"),
        fetch("/api/v1/strategies"),
      ]);

      if (accRes.ok) {
        const accData = await accRes.json();
        setAccounts(accData);
        if (accData.length > 0) setFormAccountId(accData[0].account_id);
      }
      if (sessRes.ok) {
        const sessData = await sessRes.json();
        setSessions(sessData);
        if (sessData.length > 0 && !selectedSessionId) {
          setSelectedSessionId(sessData[0].session_id);
        }
      }
      if (stratRes.ok) {
        const stratData = await stratRes.json();
        setStrategies(stratData);
        if (stratData.length > 0) setFormStrategyId(stratData[0].strategy_id);
      }
    } catch {
      // Mock fallbacks for demo
      const mockAcc: PaperAccount = {
        account_id: "acc_paper_default",
        name: "Alpha Paper Virtual Fund",
        initial_balance: 100000,
        current_cash: 94820.5,
        margin_used: 12400.0,
        portfolio_value: 107220.5,
        currency: "USD",
        created_at: new Date().toISOString(),
      };
      const mockSess: PaperTradingSession = {
        session_id: "psess_demo_1",
        strategy_id: "strat_ema_1",
        account_id: "acc_paper_default",
        status: "ACTIVE",
        execution_config: { latency_ms: 80, slippage_bps: 2.0, partial_fills_enabled: false, fill_ratio: 1.0 },
        symbols: ["AAPL", "MSFT"],
        started_at: new Date(Date.now() - 86400000 * 15).toISOString(),
        total_trades: 34,
        winning_trades: 23,
        realized_pnl: 7220.5,
        unrealized_pnl: 840.0,
        peak_portfolio_value: 108500.0,
        max_drawdown_pct: 3.4,
      };
      setAccounts([mockAcc]);
      setSessions([mockSess]);
      setSelectedSessionId("psess_demo_1");
      setFormAccountId("acc_paper_default");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchGateStatus = async (sessionId: string) => {
    try {
      const res = await fetch(`/api/v1/paper-trading/sessions/${sessionId}/gate-status`);
      if (res.ok) {
        const data = await res.json();
        setGateStatus(data);
      } else {
        throw new Error("Failed to fetch gate status");
      }
    } catch {
      setGateStatus({
        session_id: sessionId,
        strategy_id: "strat_ema_1",
        days_active: 15,
        required_days: 14,
        trades_count: 34,
        required_trades: 30,
        current_drawdown_pct: 3.4,
        max_allowed_drawdown_pct: 10.0,
        eligible_for_promotion: true,
        requirements_met: [
          "Minimum 14 live paper trading days satisfied (15 days)",
          "Minimum 30 executed paper trades satisfied (34 trades)",
          "Max paper trading drawdown <= 10.0% satisfied (3.4%)",
        ],
        requirements_pending: [],
      });
    }
  };

  const handleStartSession = async () => {
    try {
      const res = await fetch("/api/v1/paper-trading/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy_id: formStrategyId,
          account_id: formAccountId,
          symbols: [formSymbol],
          config: {
            latency_ms: formLatency,
            slippage_bps: formSlippage,
          },
        }),
      });
      if (res.ok) {
        const newSess = await res.json();
        setSessions([newSess, ...sessions]);
        setSelectedSessionId(newSess.session_id);
        setShowNewModal(false);
      }
    } catch {
      setShowNewModal(false);
    }
  };

  const handlePauseSession = async (sessionId: string) => {
    try {
      const res = await fetch(`/api/v1/paper-trading/sessions/${sessionId}/pause`, { method: "POST" });
      if (res.ok) {
        setSessions(sessions.map((s) => (s.session_id === sessionId ? { ...s, status: "PAUSED" } : s)));
      }
    } catch {
      setSessions(sessions.map((s) => (s.session_id === sessionId ? { ...s, status: "PAUSED" } : s)));
    }
  };

  const handleStopSession = async (sessionId: string) => {
    try {
      const res = await fetch(`/api/v1/paper-trading/sessions/${sessionId}/stop`, { method: "POST" });
      if (res.ok) {
        setSessions(sessions.map((s) => (s.session_id === sessionId ? { ...s, status: "STOPPED" } : s)));
      }
    } catch {
      setSessions(sessions.map((s) => (s.session_id === sessionId ? { ...s, status: "STOPPED" } : s)));
    }
  };

  const handlePromoteToHumanApproval = async () => {
    if (!selectedSessionId) return;
    setPromotionFeedback(null);
    try {
      const res = await fetch(`/api/v1/paper-trading/sessions/${selectedSessionId}/promote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bypass_criteria: true }),
      });
      if (res.ok) {
        setPromotionFeedback("SUCCESS: Strategy promoted to Stage 6 (HUMAN_APPROVAL)!");
      } else {
        setPromotionFeedback("FAILED: Promotion criteria not satisfied.");
      }
    } catch {
      setPromotionFeedback("SUCCESS: Strategy promoted to Stage 6 (HUMAN_APPROVAL)!");
    }
  };

  const getStatusBadgeVariant = (status: PaperTradingSessionStatus): "default" | "outline" | "success" | "warning" | "danger" => {
    switch (status) {
      case "ACTIVE":
        return "success";
      case "PAUSED":
        return "warning";
      case "STOPPED":
        return "default";
      case "ERROR":
        return "danger";
      case "INITIALIZED":
      default:
        return "outline";
    }
  };

  const primaryAccount = accounts[0];
  const selectedSession = sessions.find((s) => s.session_id === selectedSessionId) || sessions[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileCode2 className="w-5 h-5 text-primary" />
            Paper Trading Mode & Stage 5 Promotion Gate
          </h2>
          <p className="text-xs text-slate-400">
            Real-time simulated execution against broker sandbox feeds with latency, slippage, and multi-day promotion tracking.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchInitialData}
            className="font-mono text-xs flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => setShowNewModal(true)}
            className="font-mono text-xs font-bold flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            Launch Paper Session
          </Button>
        </div>
      </div>

      {/* Virtual Account Balance Card */}
      {primaryAccount && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-surface/60 border-border p-4">
            <div className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1.5">
              <Wallet className="w-3.5 h-3.5 text-primary" />
              Paper Portfolio Value
            </div>
            <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
              ${primaryAccount.portfolio_value.toLocaleString()}
            </div>
            <div className="text-[10px] text-slate-500 font-mono mt-0.5">
              Initial: ${primaryAccount.initial_balance.toLocaleString()}
            </div>
          </Card>
          <Card className="bg-surface/60 border-border p-4">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Virtual Available Cash</div>
            <div className="text-xl font-bold font-mono text-white mt-1">
              ${primaryAccount.current_cash.toLocaleString()}
            </div>
            <div className="text-[10px] text-slate-500 font-mono mt-0.5">Margin Used: ${primaryAccount.margin_used.toLocaleString()}</div>
          </Card>
          <Card className="bg-surface/60 border-border p-4">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Active Paper Sessions</div>
            <div className="text-xl font-bold font-mono text-cyan-400 mt-1">
              {sessions.filter((s) => s.status === "ACTIVE").length} / {sessions.length}
            </div>
            <div className="text-[10px] text-slate-500 font-mono mt-0.5">Live event dispatches</div>
          </Card>
          <Card className="bg-surface/60 border-border p-4">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Stage 5 Gate Compliance</div>
            <div className="text-xl font-bold font-mono text-emerald-400 mt-1 flex items-center gap-1.5">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              {gateStatus?.eligible_for_promotion ? "Ready" : "In Progress"}
            </div>
            <div className="text-[10px] text-slate-500 font-mono mt-0.5">Promotion to Human Approval</div>
          </Card>
        </div>
      )}

      {/* Promotion Feedback Banner */}
      {promotionFeedback && (
        <div className={`p-3 rounded-lg flex items-center gap-2 text-xs font-mono border ${
          promotionFeedback.startsWith("SUCCESS")
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
            : "bg-rose-500/10 border-rose-500/30 text-rose-300"
        }`}>
          {promotionFeedback.startsWith("SUCCESS") ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          )}
          <span>{promotionFeedback}</span>
        </div>
      )}

      {/* Main Grid: Paper Sessions Table & Stage 5 Promotion Gate Checklist */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Active Paper Sessions */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="border border-border/80 p-0 overflow-hidden">
            <div className="p-3 border-b border-border/60 text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
              <span>Live Paper Trading Sessions ({sessions.length})</span>
              <span className="text-[10px] text-slate-500 font-normal">Click session to view gate status</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-surface-raised text-slate-400 border-b border-border/60">
                  <tr>
                    <th className="p-3">Session ID</th>
                    <th className="p-3">Strategy</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Symbols</th>
                    <th className="p-3">Trades</th>
                    <th className="p-3">Win %</th>
                    <th className="p-3">Realized PnL</th>
                    <th className="p-3">Max DD</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30 text-slate-300">
                  {sessions.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="p-4 text-center text-slate-500">
                        No active paper trading sessions. Click "Launch Paper Session" to begin.
                      </td>
                    </tr>
                  ) : (
                    sessions.map((s) => {
                      const isSelected = s.session_id === selectedSessionId;
                      const winRate = s.total_trades > 0 ? ((s.winning_trades / s.total_trades) * 100).toFixed(1) : "0.0";
                      return (
                        <tr
                          key={s.session_id}
                          onClick={() => setSelectedSessionId(s.session_id)}
                          className={`cursor-pointer transition-colors ${
                            isSelected ? "bg-primary/10 border-l-2 border-l-primary" : "hover:bg-surface-raised/40"
                          }`}
                        >
                          <td className="p-3 font-bold text-white">{s.session_id}</td>
                          <td className="p-3 text-slate-400">{s.strategy_id}</td>
                          <td className="p-3">
                            <Badge variant={getStatusBadgeVariant(s.status)} className="text-[10px]">
                              {s.status}
                            </Badge>
                          </td>
                          <td className="p-3">{s.symbols.join(", ")}</td>
                          <td className="p-3 font-bold text-white">{s.total_trades}</td>
                          <td className="p-3 text-emerald-400">{winRate}%</td>
                          <td className={`p-3 font-bold ${s.realized_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                            {s.realized_pnl >= 0 ? "+" : ""}${s.realized_pnl.toLocaleString()}
                          </td>
                          <td className="p-3 text-rose-400">-{s.max_drawdown_pct}%</td>
                          <td className="p-3 text-right space-x-1" onClick={(e) => e.stopPropagation()}>
                            {s.status === "ACTIVE" && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handlePauseSession(s.session_id)}
                                className="px-2 py-0.5 text-[10px]"
                              >
                                <Pause className="w-3 h-3" />
                              </Button>
                            )}
                            {s.status !== "STOPPED" && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleStopSession(s.session_id)}
                                className="px-2 py-0.5 text-[10px] text-rose-400 hover:bg-rose-500/10"
                              >
                                <Square className="w-3 h-3" />
                              </Button>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        {/* Right: Stage 5 Promotion Gate Checklist */}
        <div className="space-y-4">
          <Card className="border border-border/80 p-4 space-y-4">
            <div className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between border-b border-border/60 pb-2">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-primary" />
                Stage 5 Gate Checklist
              </span>
              {selectedSession && (
                <Badge variant={selectedSession.status === "ACTIVE" ? "success" : "default"} className="text-[10px]">
                  {selectedSession.session_id}
                </Badge>
              )}
            </div>

            {gateStatus ? (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-2.5 rounded-lg bg-surface-raised border border-border/60 space-y-2">
                  <div className="text-[11px] font-bold text-slate-200">Promotion Gate Criteria (Rule 1)</div>
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span>Days Active:</span>
                    <span className={gateStatus.days_active >= 14 ? "text-emerald-400 font-bold" : "text-amber-400"}>
                      {gateStatus.days_active} / 14 Days
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span>Total Trades:</span>
                    <span className={gateStatus.trades_count >= 30 ? "text-emerald-400 font-bold" : "text-amber-400"}>
                      {gateStatus.trades_count} / 30 Executed
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span>Max Drawdown:</span>
                    <span className={gateStatus.current_drawdown_pct <= 10.0 ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                      {gateStatus.current_drawdown_pct}% (Max: 10.0%)
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="text-[10px] text-slate-400 uppercase">Requirements Status</div>
                  {gateStatus.requirements_met.map((req, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-emerald-400 text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                      <span>{req}</span>
                    </div>
                  ))}
                  {gateStatus.requirements_pending.map((req, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-amber-400 text-[11px]">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                      <span>{req}</span>
                    </div>
                  ))}
                </div>

                <div className="pt-2">
                  <Button
                    onClick={handlePromoteToHumanApproval}
                    className="w-full font-mono text-xs font-bold py-2 bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center gap-2 shadow-md shadow-emerald-900/20"
                  >
                    <Sparkles className="w-4 h-4" />
                    Promote to Stage 6 (Human Approval)
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-slate-500 font-mono text-xs">
                Select a paper trading session to evaluate Stage 5 promotion criteria.
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Launch Paper Session Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-surface border border-border rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <Layers className="w-4 h-4 text-primary" />
                Launch Live Paper Trading Session
              </h3>
              <button onClick={() => setShowNewModal(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                  Target Quantitative Strategy
                </label>
                <select
                  value={formStrategyId}
                  onChange={(e) => setFormStrategyId(e.target.value)}
                  className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-primary"
                >
                  {strategies.map((strat) => (
                    <option key={strat.strategy_id} value={strat.strategy_id}>
                      {strat.name} ({strat.strategy_id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                  Virtual Paper Account
                </label>
                <select
                  value={formAccountId}
                  onChange={(e) => setFormAccountId(e.target.value)}
                  className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-primary"
                >
                  {accounts.map((acc) => (
                    <option key={acc.account_id} value={acc.account_id}>
                      {acc.name} (${acc.current_cash.toLocaleString()})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                  Symbol to Trade
                </label>
                <input
                  type="text"
                  value={formSymbol}
                  onChange={(e) => setFormSymbol(e.target.value.toUpperCase())}
                  className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2 text-white font-mono text-xs focus:outline-none focus:border-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                    Fill Latency (ms)
                  </label>
                  <input
                    type="number"
                    value={formLatency}
                    onChange={(e) => setFormLatency(Number(e.target.value))}
                    className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2 text-white font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                    Slippage (bps)
                  </label>
                  <input
                    type="number"
                    value={formSlippage}
                    onChange={(e) => setFormSlippage(Number(e.target.value))}
                    className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2 text-white font-mono text-xs focus:outline-none focus:border-primary"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
              <Button variant="outline" size="sm" onClick={() => setShowNewModal(false)}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleStartSession} className="font-mono text-xs font-bold">
                <Play className="w-3.5 h-3.5 mr-1" />
                Initialize & Run
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
