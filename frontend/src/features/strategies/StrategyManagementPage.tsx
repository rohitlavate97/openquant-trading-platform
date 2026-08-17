import React, { useState, useEffect } from "react";
import {
  Cpu,
  Play,
  Pause,
  Square,
  Plus,
  TrendingUp,
  Terminal,
  Activity,
  Zap,
  Code2,
  RefreshCw,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Strategy, StrategyState } from "@/types/strategy";

const DEFAULT_EMA_CODE = `# Dual EMA Momentum Strategy
from openquant.strategies.base import BaseStrategy, StrategyContext
from openquant.domain.models.market_data import Candle
from decimal import Decimal

class EMAMomentumStrategy(BaseStrategy):
    def on_start(self, context: StrategyContext) -> None:
        context.custom_state["history"] = []
        context.custom_state["fast"] = int(context.parameters.get("fast_period", 3))
        context.custom_state["slow"] = int(context.parameters.get("slow_period", 5))
        context.log("EMA Momentum Strategy Initialized.")

    def on_bar(self, candle: Candle, context: StrategyContext) -> None:
        history = context.custom_state["history"]
        history.append(float(candle.close))
        if len(history) < context.custom_state["slow"]:
            return
        fast_sma = sum(history[-context.custom_state["fast"]:]) / context.custom_state["fast"]
        slow_sma = sum(history[-context.custom_state["slow"]:]) / context.custom_state["slow"]
        if fast_sma > slow_sma:
            context.buy(symbol=candle.symbol, quantity=Decimal("10"))
        elif fast_sma < slow_sma:
            context.sell(symbol=candle.symbol, quantity=Decimal("10"))
`;

export const StrategyManagementPage: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);
  const [runtimeLogs, setRuntimeLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Modal State
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [newStratName, setNewStratName] = useState<string>("Alpha EMA Trend");
  const [newStratDesc, setNewStratDesc] = useState<string>("Dual Moving Average Crossover Algorithm");
  const [newStratSymbols, setNewStratSymbols] = useState<string>("AAPL, MSFT");
  const [newStratCode, setNewStratCode] = useState<string>(DEFAULT_EMA_CODE);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchStrategies = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("/api/v1/strategies");
      if (res.ok) {
        const data = await res.json();
        setStrategies(data);
        if (data.length > 0 && !selectedStrategyId) {
          setSelectedStrategyId(data[0].strategy_id);
        }
      }
    } catch {
      // Fallback mock strategy
      const mock: Strategy = {
        strategy_id: "strat_demo_1",
        name: "Dual Moving Average Crossover",
        description: "Standard EMA trend following strategy on tech equities",
        author_id: "usr_quant",
        source_code: DEFAULT_EMA_CODE,
        parameters: [
          { name: "fast_period", param_type: "INT", default_value: 3, current_value: 3 },
          { name: "slow_period", param_type: "INT", default_value: 5, current_value: 5 },
        ],
        promotion_stage: "PAPER",
        state: "RUNNING",
        symbols: ["AAPL", "TSLA"],
        timeframes: ["1m"],
        account_id: "acc_main",
        broker_id: "paper_broker",
        total_trades: 14,
        winning_trades: 9,
        total_pnl: 1420.5,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setStrategies([mock]);
      setSelectedStrategyId("strat_demo_1");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchLogs = async (stratId: string) => {
    try {
      const res = await fetch(`/api/v1/strategies/${stratId}/logs`);
      if (res.ok) {
        const data = await res.json();
        setRuntimeLogs(data.logs || []);
      }
    } catch {
      setRuntimeLogs([
        `[${stratId}] Strategy started successfully`,
        `[${stratId}] Bullish Crossover on AAPL: Fast SMA=185.60 > Slow SMA=183.20`,
        `[${stratId}] Order BUY AAPL qty:10 filled @ $185.70`,
      ]);
    }
  };

  useEffect(() => {
    fetchStrategies();
  }, []);

  useEffect(() => {
    if (selectedStrategyId) {
      fetchLogs(selectedStrategyId);
    }
  }, [selectedStrategyId]);

  const handleStartStrategy = async (stratId: string) => {
    try {
      await fetch(`/api/v1/strategies/${stratId}/start`, { method: "POST" });
      fetchStrategies();
      fetchLogs(stratId);
    } catch {}
  };

  const handlePauseStrategy = async (stratId: string) => {
    try {
      await fetch(`/api/v1/strategies/${stratId}/pause`, { method: "POST" });
      fetchStrategies();
    } catch {}
  };

  const handleStopStrategy = async (stratId: string) => {
    try {
      await fetch(`/api/v1/strategies/${stratId}/stop`, { method: "POST" });
      fetchStrategies();
      fetchLogs(stratId);
    } catch {}
  };

  const handleCreateStrategy = async () => {
    setFormError(null);
    try {
      const symbolsArray = newStratSymbols.split(",").map((s) => s.trim().toUpperCase()).filter(Boolean);
      const res = await fetch("/api/v1/strategies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newStratName,
          description: newStratDesc,
          source_code: newStratCode,
          symbols: symbolsArray,
          parameters: [
            { name: "fast_period", param_type: "INT", default_value: 3, current_value: 3 },
            { name: "slow_period", param_type: "INT", default_value: 5, current_value: 5 },
          ],
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        setFormError(err.detail || "Failed to create strategy");
        return;
      }

      setShowCreateModal(false);
      fetchStrategies();
    } catch (e: any) {
      setFormError(e.message || "Failed to create strategy");
    }
  };

  const getStateBadgeVariant = (state: StrategyState): "default" | "outline" | "success" | "warning" | "danger" => {
    switch (state) {
      case "RUNNING":
        return "success";
      case "PAUSED":
        return "warning";
      case "STOPPED":
        return "default";
      case "ERROR":
        return "danger";
      case "INITIALIZED":
      case "DRAFT":
      default:
        return "outline";
    }
  };

  const selectedStrategy = strategies.find((s) => s.strategy_id === selectedStrategyId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-primary" />
            Strategy Execution Engine
          </h2>
          <p className="text-xs text-slate-400">
            Real-time Python quantitative strategy lifecycle, event loop dispatching, and promotion pipeline.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={fetchStrategies}
            disabled={isLoading}
            className="font-mono text-xs flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            size="sm"
            variant="primary"
            onClick={() => setShowCreateModal(true)}
            className="font-mono text-xs font-bold flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            New Strategy
          </Button>
        </div>
      </div>

      {/* Strategy Grid & Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Strategy List Cards */}
        <div className="space-y-3 lg:col-span-1">
          <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between px-1">
            <span>Active Strategies ({strategies.length})</span>
          </div>

          {strategies.length === 0 ? (
            <Card className="p-6 text-center text-xs text-slate-500 font-mono">
              No registered strategies. Click "New Strategy" to deploy one.
            </Card>
          ) : (
            strategies.map((strat) => {
              const isSelected = strat.strategy_id === selectedStrategyId;
              return (
                <Card
                  key={strat.strategy_id}
                  onClick={() => setSelectedStrategyId(strat.strategy_id)}
                  className={`p-4 cursor-pointer transition-all space-y-3 border ${
                    isSelected
                      ? "border-primary bg-primary/5 shadow-md shadow-primary/10"
                      : "border-border/80 hover:border-slate-700 bg-surface"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-white leading-tight">{strat.name}</h4>
                      <span className="text-[10px] font-mono text-slate-400">
                        {strat.strategy_id} • Stage: {strat.promotion_stage}
                      </span>
                    </div>
                    <Badge variant={getStateBadgeVariant(strat.state)} className="font-mono text-[10px]">
                      {strat.state}
                    </Badge>
                  </div>

                  <p className="text-xs text-slate-300 line-clamp-2">{strat.description || "No description provided."}</p>

                  <div className="flex items-center justify-between pt-1 border-t border-border/60 text-[11px] font-mono text-slate-400">
                    <span>Symbols: {strat.symbols.join(", ")}</span>
                    <span className={Number(strat.total_pnl) >= 0 ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                      PnL: ${Number(strat.total_pnl).toFixed(2)}
                    </span>
                  </div>
                </Card>
              );
            })
          )}
        </div>

        {/* Right Column: Selected Strategy Details & Runtime Console (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          {selectedStrategy ? (
            <>
              {/* Controls & Overview Banner */}
              <Card className="p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/60 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-white">{selectedStrategy.name}</h3>
                      <Badge variant={getStateBadgeVariant(selectedStrategy.state)} className="font-mono text-xs">
                        {selectedStrategy.state}
                      </Badge>
                      <Badge variant="outline" className="font-mono text-xs border-primary/40 text-primary">
                        Stage: {selectedStrategy.promotion_stage}
                      </Badge>
                    </div>
                    <span className="text-xs text-slate-400 font-mono">
                      Target Account: {selectedStrategy.account_id} • Broker: {selectedStrategy.broker_id}
                    </span>
                  </div>

                  {/* Lifecycle Controls */}
                  <div className="flex items-center gap-2">
                    {selectedStrategy.state !== "RUNNING" && (
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleStartStrategy(selectedStrategy.strategy_id)}
                        className="font-mono text-xs flex items-center gap-1.5"
                      >
                        <Play className="w-3.5 h-3.5" /> Start
                      </Button>
                    )}
                    {selectedStrategy.state === "RUNNING" && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handlePauseStrategy(selectedStrategy.strategy_id)}
                        className="font-mono text-xs flex items-center gap-1.5"
                      >
                        <Pause className="w-3.5 h-3.5" /> Pause
                      </Button>
                    )}
                    {selectedStrategy.state !== "STOPPED" && (
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => handleStopStrategy(selectedStrategy.strategy_id)}
                        className="font-mono text-xs flex items-center gap-1.5"
                      >
                        <Square className="w-3.5 h-3.5" /> Stop
                      </Button>
                    )}
                  </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 bg-surface-raised rounded-xl border border-border">
                    <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
                      <TrendingUp className="w-3 h-3 text-primary" /> Total Realized PnL
                    </span>
                    <div className="text-base font-bold text-white font-mono mt-1">
                      ${Number(selectedStrategy.total_pnl).toFixed(2)}
                    </div>
                  </div>
                  <div className="p-3 bg-surface-raised rounded-xl border border-border">
                    <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
                      <Activity className="w-3 h-3 text-primary" /> Total Executed Trades
                    </span>
                    <div className="text-base font-bold text-white font-mono mt-1">
                      {selectedStrategy.total_trades}
                    </div>
                  </div>
                  <div className="p-3 bg-surface-raised rounded-xl border border-border">
                    <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
                      <Zap className="w-3 h-3 text-emerald-400" /> Win Rate
                    </span>
                    <div className="text-base font-bold text-emerald-400 font-mono mt-1">
                      {selectedStrategy.total_trades > 0
                        ? `${((selectedStrategy.winning_trades / selectedStrategy.total_trades) * 100).toFixed(0)}%`
                        : "0%"}
                    </div>
                  </div>
                  <div className="p-3 bg-surface-raised rounded-xl border border-border">
                    <span className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
                      <Code2 className="w-3 h-3 text-primary" /> Symbols
                    </span>
                    <div className="text-xs font-bold text-white font-mono mt-1.5 truncate">
                      {selectedStrategy.symbols.join(", ")}
                    </div>
                  </div>
                </div>
              </Card>

              {/* Source Code & Parameters */}
              <Card className="p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-border/60 pb-2">
                  <h4 className="text-xs font-bold text-white flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-primary" />
                    Python Strategy Implementation
                  </h4>
                  <Badge variant="outline" className="font-mono text-[10px]">
                    {selectedStrategy.parameters.length} Parameters Configured
                  </Badge>
                </div>
                <pre className="p-3 bg-slate-950 rounded-xl border border-border text-slate-200 font-mono text-xs leading-relaxed max-h-56 overflow-y-auto">
                  {selectedStrategy.source_code}
                </pre>
              </Card>

              {/* Real-time Diagnostics Terminal */}
              <Card className="p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-border/60 pb-2">
                  <h4 className="text-xs font-bold text-white flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-primary" />
                    Strategy Runtime Event Stream & Logs
                  </h4>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => fetchLogs(selectedStrategy.strategy_id)}
                    className="text-[10px] font-mono text-slate-400 h-6 px-2"
                  >
                    Refresh Logs
                  </Button>
                </div>

                <div className="p-3 bg-slate-950 rounded-xl border border-border font-mono text-xs max-h-48 overflow-y-auto space-y-1">
                  {runtimeLogs.length === 0 ? (
                    <div className="text-slate-500 italic">No events or logs emitted yet.</div>
                  ) : (
                    runtimeLogs.map((log, i) => (
                      <div key={i} className="text-emerald-400 flex items-start gap-2">
                        <span className="text-slate-600 select-none">&gt;</span>
                        <span>{log}</span>
                      </div>
                    ))
                  )}
                </div>
              </Card>
            </>
          ) : (
            <Card className="p-8 text-center text-slate-500 font-mono text-xs">
              Select a strategy to view its runtime console and performance metrics.
            </Card>
          )}
        </div>
      </div>

      {/* Create Strategy Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <Card className="w-full max-w-2xl p-6 space-y-4 bg-surface border border-border shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-primary" /> Deploy Quantitative Strategy
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white font-mono text-sm"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 font-mono text-xs">
                {formError}
              </div>
            )}

            <div className="space-y-3 font-mono text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Strategy Name</label>
                  <input
                    type="text"
                    value={newStratName}
                    onChange={(e) => setNewStratName(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-raised border border-border rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Subscribed Symbols (comma separated)</label>
                  <input
                    type="text"
                    value={newStratSymbols}
                    onChange={(e) => setNewStratSymbols(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-raised border border-border rounded-lg text-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Description</label>
                <input
                  type="text"
                  value={newStratDesc}
                  onChange={(e) => setNewStratDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-raised border border-border rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Python Strategy Code (AST Linted)</label>
                <textarea
                  value={newStratCode}
                  onChange={(e) => setNewStratCode(e.target.value)}
                  rows={10}
                  className="w-full p-3 bg-slate-950 border border-border rounded-xl text-slate-100 text-xs font-mono leading-relaxed"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
              <Button size="sm" variant="ghost" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button size="sm" variant="primary" onClick={handleCreateStrategy}>
                Validate & Deploy Strategy
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
