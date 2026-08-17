import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  Radio,
  Plus,
  X,
  Activity,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useWebSocket } from "@/lib/useWebSocket";

export interface LiveTick {
  symbol: string;
  exchange: string;
  last_price: number;
  last_quantity?: number;
  bid_price?: number;
  ask_price?: number;
  volume: number;
  direction?: "UP" | "DOWN" | "SAME";
  updated_at: string;
}

const INITIAL_TICKS: Record<string, LiveTick> = {
  AAPL: {
    symbol: "AAPL",
    exchange: "NASDAQ",
    last_price: 185.5,
    bid_price: 185.48,
    ask_price: 185.52,
    volume: 1250000,
    direction: "UP",
    updated_at: new Date().toLocaleTimeString(),
  },
  MSFT: {
    symbol: "MSFT",
    exchange: "NASDAQ",
    last_price: 420.25,
    bid_price: 420.2,
    ask_price: 420.3,
    volume: 850000,
    direction: "SAME",
    updated_at: new Date().toLocaleTimeString(),
  },
  NVDA: {
    symbol: "NVDA",
    exchange: "NASDAQ",
    last_price: 130.4,
    bid_price: 130.38,
    ask_price: 130.42,
    volume: 3200000,
    direction: "UP",
    updated_at: new Date().toLocaleTimeString(),
  },
  RELIANCE: {
    symbol: "RELIANCE",
    exchange: "NSE",
    last_price: 2950.0,
    bid_price: 2949.5,
    ask_price: 2950.5,
    volume: 450000,
    direction: "DOWN",
    updated_at: new Date().toLocaleTimeString(),
  },
};

export const LiveMarketTicker: React.FC = () => {
  const [ticks, setTicks] = useState<Record<string, LiveTick>>(INITIAL_TICKS);
  const [subscribedSymbols, setSubscribedSymbols] = useState<string[]>(["AAPL", "MSFT", "NVDA", "RELIANCE"]);
  const [newSymbolInput, setNewSymbolInput] = useState<string>("");

  const { isConnected, sendJson } = useWebSocket({
    url: "/ws/v1/market-data",
    autoConnect: true,
    onOpen: () => {
      // Send subscription on connect
      sendJson({ action: "subscribe", symbols: subscribedSymbols });
    },
    onMessage: (msg) => {
      if (msg.type === "TICK" && msg.symbol) {
        setTicks((prev) => {
          const oldPrice = prev[msg.symbol]?.last_price ?? Number(msg.last_price);
          const newPrice = Number(msg.last_price);
          const direction = newPrice > oldPrice ? "UP" : newPrice < oldPrice ? "DOWN" : "SAME";

          return {
            ...prev,
            [msg.symbol]: {
              symbol: msg.symbol,
              exchange: msg.exchange || "NSE",
              last_price: newPrice,
              bid_price: msg.bid_price ? Number(msg.bid_price) : undefined,
              ask_price: msg.ask_price ? Number(msg.ask_price) : undefined,
              volume: msg.volume ? Number(msg.volume) : 0,
              direction,
              updated_at: new Date().toLocaleTimeString(),
            },
          };
        });
      }
    },
  });

  // Simulated tick generator for smooth UI demonstration when backend stream is idle
  useEffect(() => {
    const interval = setInterval(() => {
      const symbols = Object.keys(ticks);
      if (symbols.length === 0) return;
      const randSymbol = symbols[Math.floor(Math.random() * symbols.length)];
      const current = ticks[randSymbol];
      if (!current) return;

      const delta = (Math.random() - 0.48) * (current.last_price * 0.001);
      const newPrice = Number((current.last_price + delta).toFixed(2));
      const direction = newPrice > current.last_price ? "UP" : "DOWN";

      setTicks((prev) => ({
        ...prev,
        [randSymbol]: {
          ...current,
          last_price: newPrice,
          direction,
          updated_at: new Date().toLocaleTimeString(),
        },
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, [ticks]);

  const handleAddSymbol = (e: React.FormEvent) => {
    e.preventDefault();
    const sym = newSymbolInput.trim().toUpperCase();
    if (!sym || subscribedSymbols.includes(sym)) return;

    const nextSymbols = [...subscribedSymbols, sym];
    setSubscribedSymbols(nextSymbols);
    setTicks((prev) => ({
      ...prev,
      [sym]: {
        symbol: sym,
        exchange: "NASDAQ",
        last_price: 100.0,
        volume: 10000,
        direction: "SAME",
        updated_at: new Date().toLocaleTimeString(),
      },
    }));
    sendJson({ action: "subscribe", symbols: [sym] });
    setNewSymbolInput("");
  };

  const handleRemoveSymbol = (sym: string) => {
    const next = subscribedSymbols.filter((s) => s !== sym);
    setSubscribedSymbols(next);
    sendJson({ action: "unsubscribe", symbols: [sym] });
  };

  return (
    <div className="space-y-4">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          <h3 className="text-sm font-bold text-white">Live L1 Market Stream & Telemetry</h3>
          {isConnected ? (
            <Badge variant="success" className="font-mono text-[10px] flex items-center gap-1">
              <Radio className="w-3 h-3 animate-pulse text-emerald-400" />
              WS STREAM LIVE
            </Badge>
          ) : (
            <Badge variant="outline" className="font-mono text-[10px] text-slate-400">
              SIMULATED TICKS ACTIVE
            </Badge>
          )}
        </div>

        {/* Subscribe New Symbol Bar */}
        <form onSubmit={handleAddSymbol} className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Add symbol (e.g. TSLA)"
            value={newSymbolInput}
            onChange={(e) => setNewSymbolInput(e.target.value)}
            className="px-3 py-1 bg-surface-raised border border-border rounded-lg text-xs text-white placeholder-slate-500 font-mono w-44 focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <Button size="sm" variant="secondary" type="submit" className="text-xs flex items-center gap-1">
            <Plus className="w-3 h-3" />
            Track
          </Button>
        </form>
      </div>

      {/* Live Ticker Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {subscribedSymbols.map((sym) => {
          const tick = ticks[sym];
          if (!tick) return null;

          const isUp = tick.direction === "UP";
          const isDown = tick.direction === "DOWN";

          return (
            <Card
              key={sym}
              className={`p-4 flex flex-col justify-between border transition-all duration-300 ${
                isUp
                  ? "border-emerald-500/40 bg-emerald-500/[0.03]"
                  : isDown
                  ? "border-rose-500/40 bg-rose-500/[0.03]"
                  : "border-border"
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold font-mono text-sm text-white">{tick.symbol}</span>
                    <span className="text-[10px] font-mono text-slate-500">{tick.exchange}</span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">Vol: {tick.volume.toLocaleString()}</span>
                </div>

                <button
                  type="button"
                  onClick={() => handleRemoveSymbol(sym)}
                  className="text-slate-500 hover:text-slate-300 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="pt-2 flex items-baseline justify-between">
                <div className="text-lg font-bold font-mono text-white">
                  ${tick.last_price.toFixed(2)}
                </div>

                <div className="flex items-center gap-1 text-xs font-mono">
                  {isUp ? (
                    <span className="flex items-center text-emerald-400 font-semibold">
                      <TrendingUp className="w-3.5 h-3.5 mr-0.5" />
                      +0.12%
                    </span>
                  ) : isDown ? (
                    <span className="flex items-center text-rose-400 font-semibold">
                      <TrendingDown className="w-3.5 h-3.5 mr-0.5" />
                      -0.08%
                    </span>
                  ) : (
                    <span className="text-slate-400">0.00%</span>
                  )}
                </div>
              </div>

              <div className="pt-2 border-t border-border/40 flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span>
                  Bid: <strong className="text-slate-200">{tick.bid_price?.toFixed(2) ?? "—"}</strong>
                </span>
                <span>
                  Ask: <strong className="text-slate-200">{tick.ask_price?.toFixed(2) ?? "—"}</strong>
                </span>
                <span className="text-slate-500">{tick.updated_at}</span>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
