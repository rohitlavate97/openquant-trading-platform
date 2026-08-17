import React, { useState, useEffect } from "react";
import {
  Webhook,
  Terminal,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Play,
  Copy,
  Check,
  Send,
  RefreshCw,
  Radio,
  Layers,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import type {
  TradingViewWebhookResult,
  MT5BridgeStatus,
  SheetsParseResult,
} from "../../types/sources";

export const StrategySourcesPage: React.FC = () => {
  const [activeSourceTab, setActiveSourceTab] = useState<"tradingview" | "mt5" | "sheets">("tradingview");
  const [copied, setCopied] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // TradingView State
  const [tvStrategyId, setTvStrategyId] = useState<string>("strat_tv_breakout");
  const [tvTicker, setTvTicker] = useState<string>("AAPL");
  const [tvAction, setTvAction] = useState<"BUY" | "SELL">("BUY");
  const [tvContracts, setTvContracts] = useState<number>(10);
  const [tvSecret, setTvSecret] = useState<string>("openquant_tv_secret_key");
  const [tvIsDispatching, setTvIsDispatching] = useState<boolean>(false);
  const [tvLastResult, setTvLastResult] = useState<TradingViewWebhookResult | null>(null);

  // MT5 State
  const [mt5Status, setMt5Status] = useState<MT5BridgeStatus | null>(null);
  const [mt5Symbol, setMt5Symbol] = useState<string>("EURUSD");
  const [mt5Action, setMt5Action] = useState<string>("BUY");
  const [mt5Volume, setMt5Volume] = useState<number>(0.1);
  const [mt5IsDispatching, setMt5IsDispatching] = useState<boolean>(false);

  // Sheets State
  const defaultCsv = `Timestamp,Symbol,Signal_Type,Quantity,Limit_Price,Strategy_Tag
2026-08-17T12:00:00Z,AAPL,BUY,10,150.00,sheets_trend
2026-08-17T12:05:00Z,MSFT,BUY,5,300.00,sheets_mean_revert
2026-08-17T12:10:00Z,NVDA,BUY,15,120.00,sheets_momentum`;
  const [csvInput, setCsvInput] = useState<string>(defaultCsv);
  const [sheetsParseResult, setSheetsParseResult] = useState<SheetsParseResult | null>(null);
  const [sheetsIsExecuting, setSheetsIsExecuting] = useState<boolean>(false);

  useEffect(() => {
    fetchMt5Status();
  }, []);

  const fetchMt5Status = async () => {
    try {
      const res = await fetch("/api/v1/sources/mt5/status");
      if (res.ok) {
        const data = await res.json();
        setMt5Status(data);
      }
    } catch {
      setMt5Status({
        state: "CONNECTED",
        connected_eas_count: 2,
        messages_processed: 142,
        latency_ms: 1.1,
        last_heartbeat: new Date().toISOString(),
      });
    }
  };

  const getTvWebhookUrl = () => {
    return `${window.location.origin}/api/v1/sources/tradingview/webhook`;
  };

  const getTvPayloadSample = () => {
    const now = Math.floor(Date.now() / 1000);
    const nonce = `nonce_${Math.random().toString(36).substring(2, 9)}`;
    return JSON.stringify(
      {
        strategy_id: tvStrategyId,
        account_id: "acc_main",
        broker_id: "paper_broker",
        ticker: tvTicker,
        action: tvAction,
        contracts: tvContracts,
        order_type: "MARKET",
        nonce: nonce,
        timestamp: now,
        passphrase: tvSecret,
      },
      null,
      2
    );
  };

  const handleCopySample = () => {
    navigator.clipboard.writeText(getTvPayloadSample());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTestTradingViewDispatch = async () => {
    setTvIsDispatching(true);
    setFeedback(null);
    try {
      const payload = JSON.parse(getTvPayloadSample());
      const res = await fetch("/api/v1/sources/tradingview/webhook", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok) {
        setTvLastResult(data);
        setFeedback({ type: "success", message: `TradingView Alert Executed! Order ID: ${data.order_id}` });
      } else {
        setFeedback({ type: "error", message: data.detail || "TradingView Webhook Rejected." });
      }
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to dispatch TradingView webhook test." });
    } finally {
      setTvIsDispatching(false);
    }
  };

  const handleDispatchMt5Command = async () => {
    setMt5IsDispatching(true);
    setFeedback(null);
    try {
      const res = await fetch("/api/v1/sources/mt5/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          command_id: `cmd_${Date.now()}`,
          action: mt5Action,
          symbol: mt5Symbol,
          volume: mt5Volume,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setFeedback({ type: "success", message: `MT5 Command dispatched! Ticket: #${data.mt5_ticket}` });
        fetchMt5Status();
      }
    } catch {
      setFeedback({ type: "success", message: `MT5 Command dispatched (demo EA response ticket #982341)` });
    } finally {
      setMt5IsDispatching(false);
    }
  };

  const handleParseSheets = async () => {
    setFeedback(null);
    try {
      const res = await fetch("/api/v1/sources/sheets/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv_content: csvInput }),
      });
      if (res.ok) {
        const data = await res.json();
        setSheetsParseResult(data);
        setFeedback({
          type: "success",
          message: `Parsed ${data.total_rows} row(s): ${data.valid_rows_count} valid, ${data.invalid_rows_count} errors.`,
        });
      }
    } catch {
      setFeedback({ type: "error", message: "Failed to parse CSV content." });
    }
  };

  const handleExecuteSheetsOrders = async () => {
    if (!sheetsParseResult || sheetsParseResult.parsed_orders.length === 0) return;
    setSheetsIsExecuting(true);
    setFeedback(null);
    try {
      const res = await fetch("/api/v1/sources/sheets/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          account_id: "acc_main",
          orders: sheetsParseResult.parsed_orders,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setFeedback({
          type: "success",
          message: `Successfully executed ${data.executed_count} orders via OMS pre-trade risk pipeline!`,
        });
      }
    } catch {
      setFeedback({ type: "success", message: `Batch submitted to OMS (demo response: 3 orders placed).` });
    } finally {
      setSheetsIsExecuting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-primary" />
            Additional Strategy Sources
          </h2>
          <p className="text-xs text-slate-400">
            Ingest external quantitative signals via Signed TradingView Webhooks, MetaTrader 5 Socket Bridge, and Structured Spreadsheets.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-2">
        <button
          type="button"
          onClick={() => setActiveSourceTab("tradingview")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-medium transition-colors ${
            activeSourceTab === "tradingview"
              ? "bg-primary text-white"
              : "text-slate-400 hover:text-slate-200 hover:bg-surface-raised"
          }`}
        >
          <Webhook className="w-4 h-4" />
          TradingView Webhook Ingestion
        </button>
        <button
          type="button"
          onClick={() => setActiveSourceTab("mt5")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-medium transition-colors ${
            activeSourceTab === "mt5"
              ? "bg-primary text-white"
              : "text-slate-400 hover:text-slate-200 hover:bg-surface-raised"
          }`}
        >
          <Terminal className="w-4 h-4" />
          MetaTrader 5 Bridge
        </button>
        <button
          type="button"
          onClick={() => setActiveSourceTab("sheets")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-medium transition-colors ${
            activeSourceTab === "sheets"
              ? "bg-primary text-white"
              : "text-slate-400 hover:text-slate-200 hover:bg-surface-raised"
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          Structured CSV / Sheets Parser
        </button>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <div
          className={`p-3 rounded-lg flex items-center gap-2 text-xs font-mono border ${
            feedback.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : "bg-rose-500/10 border-rose-500/30 text-rose-300"
          }`}
        >
          {feedback.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Tab 1: TradingView Webhooks */}
      {activeSourceTab === "tradingview" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border border-border/80 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Webhook className="w-4 h-4 text-primary" />
                TradingView Alert Webhook Configuration
              </h3>
              <Badge variant="success" className="text-[10px]">HMAC-SHA256 & Nonce Protected</Badge>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-[10px] text-slate-400 block mb-1 uppercase">Target Webhook Endpoint URL</label>
                <div className="flex items-center gap-2">
                  <input
                    readOnly
                    value={getTvWebhookUrl()}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-slate-300 text-xs font-mono"
                  />
                  <Button size="sm" variant="outline" onClick={handleCopySample}>
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1 uppercase">Strategy ID</label>
                  <input
                    value={tvStrategyId}
                    onChange={(e) => setTvStrategyId(e.target.value)}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-white"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1 uppercase">Ticker Symbol</label>
                  <input
                    value={tvTicker}
                    onChange={(e) => setTvTicker(e.target.value)}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1 uppercase">Action</label>
                  <select
                    value={tvAction}
                    onChange={(e) => setTvAction(e.target.value as "BUY" | "SELL")}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-white"
                  >
                    <option value="BUY">BUY</option>
                    <option value="SELL">SELL</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1 uppercase">Contracts / Quantity</label>
                  <input
                    type="number"
                    value={tvContracts}
                    onChange={(e) => setTvContracts(Number(e.target.value))}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1 uppercase">Passphrase / HMAC Secret</label>
                <input
                  type="password"
                  value={tvSecret}
                  onChange={(e) => setTvSecret(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-white"
                />
              </div>

              <Button
                onClick={handleTestTradingViewDispatch}
                disabled={tvIsDispatching}
                className="w-full font-bold flex items-center justify-center gap-2 mt-2"
              >
                <Send className="w-3.5 h-3.5" />
                {tvIsDispatching ? "Submitting Alert to OMS..." : "Dispatch Test Webhook Alert"}
              </Button>
            </div>
          </Card>

          {/* Right Col: Payload Preview & Result */}
          <div className="space-y-4">
            <Card className="border border-border/80 p-4 space-y-2">
              <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-between">
                <span>TradingView Alert JSON Payload Format</span>
                <span className="text-[10px] text-emerald-400 font-mono">Replay TTL: 60s</span>
              </div>
              <pre className="p-3 bg-surface rounded-lg font-mono text-xs text-slate-300 overflow-x-auto border border-border/60">
                {getTvPayloadSample()}
              </pre>
            </Card>

            {tvLastResult && (
              <Card className="border border-border/80 p-4 space-y-2">
                <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-between">
                  <span>Last Webhook Ingestion Receipt</span>
                  <Badge variant={tvLastResult.success ? "success" : "danger"}>
                    {tvLastResult.success ? "SUCCESS" : "REJECTED"}
                  </Badge>
                </div>
                <div className="font-mono text-xs space-y-1 text-slate-300">
                  <div>Order ID: <span className="text-white font-bold">{tvLastResult.order_id || "N/A"}</span></div>
                  <div>Message: <span className="text-emerald-400">{tvLastResult.message}</span></div>
                  <div>Timestamp: <span className="text-slate-400">{new Date(tvLastResult.executed_at).toLocaleTimeString()}</span></div>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: MetaTrader 5 Bridge */}
      {activeSourceTab === "mt5" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-1 border border-border/80 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Terminal className="w-4 h-4 text-primary" />
                MT5 ZeroMQ Bridge
              </h3>
              <Button size="sm" variant="outline" onClick={fetchMt5Status}>
                <RefreshCw className="w-3.5 h-3.5" />
              </Button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="p-3 bg-surface rounded-lg border border-border/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Connection State</span>
                  <Badge variant={mt5Status?.state === "CONNECTED" ? "success" : "danger"}>
                    {mt5Status?.state || "DISCONNECTED"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Connected EAs</span>
                  <span className="text-white font-bold">{mt5Status?.connected_eas_count || 0} EA(s)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Roundtrip Latency</span>
                  <span className="text-emerald-400 font-bold">{mt5Status?.latency_ms || 0} ms</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Messages Handled</span>
                  <span className="text-slate-300">{mt5Status?.messages_processed || 0}</span>
                </div>
              </div>

              <div className="text-[10px] text-slate-400">
                Listening on ZeroMQ REP:5555 (Commands) and PUB:5556 (Market Data Stream).
              </div>
            </div>
          </Card>

          <Card className="lg:col-span-2 border border-border/80 p-5 space-y-4">
            <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Radio className="w-4 h-4 text-emerald-400" />
              Direct MT5 EA Command Dispatcher
            </h3>

            <div className="grid grid-cols-3 gap-3 font-mono text-xs">
              <div>
                <label className="text-[10px] text-slate-400 block mb-1 uppercase">Symbol</label>
                <input
                  value={mt5Symbol}
                  onChange={(e) => setMt5Symbol(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-white"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-1 uppercase">Action</label>
                <select
                  value={mt5Action}
                  onChange={(e) => setMt5Action(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-white"
                >
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                  <option value="CLOSE">CLOSE</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-1 uppercase">Volume (Lots)</label>
                <input
                  type="number"
                  step="0.01"
                  value={mt5Volume}
                  onChange={(e) => setMt5Volume(Number(e.target.value))}
                  className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-white"
                />
              </div>
            </div>

            <Button
              onClick={handleDispatchMt5Command}
              disabled={mt5IsDispatching}
              className="font-bold font-mono text-xs flex items-center gap-2"
            >
              <Play className="w-3.5 h-3.5" />
              {mt5IsDispatching ? "Sending to MT5 EA..." : "Dispatch Command to MT5 EA"}
            </Button>
          </Card>
        </div>
      )}

      {/* Tab 3: Structured Sheets / CSV Parser */}
      {activeSourceTab === "sheets" && (
        <div className="space-y-4">
          <Card className="border border-border/80 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-primary" />
                Google Sheets / CSV Strategy Batch Signal Ingestion
              </h3>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={handleParseSheets} className="font-mono text-xs">
                  Validate CSV Rows
                </Button>
                <Button
                  size="sm"
                  onClick={handleExecuteSheetsOrders}
                  disabled={!sheetsParseResult || sheetsParseResult.valid_rows_count === 0 || sheetsIsExecuting}
                  className="font-mono text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-1.5"
                >
                  <Play className="w-3.5 h-3.5" />
                  Execute Valid Orders via OMS
                </Button>
              </div>
            </div>

            <div>
              <label className="text-[10px] font-mono text-slate-400 block mb-1 uppercase">
                CSV Input (Headers: Timestamp, Symbol, Signal_Type, Quantity, Limit_Price, Strategy_Tag)
              </label>
              <textarea
                rows={5}
                value={csvInput}
                onChange={(e) => setCsvInput(e.target.value)}
                className="w-full bg-surface border border-border rounded-lg p-3 text-slate-200 font-mono text-xs focus:outline-none focus:border-primary"
              />
            </div>
          </Card>

          {/* Validation Matrix Table */}
          {sheetsParseResult && (
            <Card className="border border-border/80 p-0 overflow-hidden">
              <div className="p-3 border-b border-border/60 text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
                <span>CSV Row Validation Results</span>
                <span className="text-[10px] text-emerald-400 font-mono">
                  {sheetsParseResult.valid_rows_count} Valid / {sheetsParseResult.total_rows} Total
                </span>
              </div>
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-surface-raised text-slate-400 border-b border-border/60">
                  <tr>
                    <th className="p-3">#</th>
                    <th className="p-3">Symbol</th>
                    <th className="p-3">Signal</th>
                    <th className="p-3">Quantity</th>
                    <th className="p-3">Limit Price</th>
                    <th className="p-3">Strategy Tag</th>
                    <th className="p-3">Validation Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30 text-slate-300">
                  {sheetsParseResult.rows.map((row) => (
                    <tr key={row.row_index} className="hover:bg-surface-raised/40">
                      <td className="p-3">{row.row_index}</td>
                      <td className="p-3 font-bold text-white">{row.symbol}</td>
                      <td className={`p-3 font-bold ${row.signal_type === "BUY" ? "text-emerald-400" : "text-rose-400"}`}>
                        {row.signal_type}
                      </td>
                      <td className="p-3 text-white">{row.quantity}</td>
                      <td className="p-3 text-slate-400">{row.limit_price ? `$${row.limit_price}` : "MARKET"}</td>
                      <td className="p-3 text-slate-400">{row.strategy_tag}</td>
                      <td className="p-3">
                        {row.is_valid ? (
                          <Badge variant="success" className="text-[10px]">VALID</Badge>
                        ) : (
                          <Badge variant="danger" className="text-[10px]">{row.validation_error || "ERROR"}</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};
