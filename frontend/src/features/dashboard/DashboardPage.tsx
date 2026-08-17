import React from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Cpu,
  Link,
  Layers,
  CheckCircle,
  AlertTriangle,
  FileCode2,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { PromotionGateOverview } from "../promotion-gate/PromotionGateOverview";
import { SystemInfo } from "@/types";

interface DashboardPageProps {
  systemInfo: SystemInfo | null;
  killSwitchActive: boolean;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  systemInfo,
  killSwitchActive,
}) => {
  return (
    <div className="space-y-6">
      {/* Top Banner Alert if Kill Switch is Active */}
      {killSwitchActive && (
        <div className="p-4 bg-danger/20 border border-danger/60 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-6 h-6 text-danger animate-pulse" />
            <div>
              <div className="text-sm font-bold text-white">
                GLOBAL EMERGENCY KILL SWITCH IS ACTIVE
              </div>
              <p className="text-xs text-slate-300">
                All order placement across all strategies, accounts, and brokers is hard-blocked pre-trade.
              </p>
            </div>
          </div>
          <Badge variant="danger">TRADING HALTED</Badge>
        </div>
      )}

      {/* Hero Welcome & Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="flex items-center gap-4">
          <div className="p-3 bg-primary/20 text-primary rounded-xl">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs text-slate-400 font-medium">Pre-Trade Risk Engine</div>
            <div className="text-lg font-bold text-white">Hard Stops Active</div>
            <div className="text-[11px] text-emerald-400 flex items-center gap-1 mt-0.5">
              <CheckCircle className="w-3 h-3" /> Max Drawdown 5.0%
            </div>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-cyan-500/20 text-cyan-400 rounded-xl">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs text-slate-400 font-medium">Strategy Sandbox</div>
            <div className="text-lg font-bold text-white">AST Strict Mode</div>
            <div className="text-[11px] text-cyan-400 mt-0.5">
              {systemInfo?.sandbox.max_cpu_seconds ?? 30}s CPU / {systemInfo?.sandbox.max_memory_mb ?? 512}MB Quota
            </div>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-indigo-500/20 text-indigo-400 rounded-xl">
            <Link className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs text-slate-400 font-medium">Broker Adapters</div>
            <div className="text-lg font-bold text-white">Certified Only</div>
            <div className="text-[11px] text-indigo-400 mt-0.5">
              Unified Adapter Layer
            </div>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-amber-500/20 text-amber-400 rounded-xl">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs text-slate-400 font-medium">Strategy Gate</div>
            <div className="text-lg font-bold text-white">7-Stage Lifecycle</div>
            <div className="text-[11px] text-amber-400 mt-0.5">
              Live Disabled by Default
            </div>
          </div>
        </Card>
      </div>

      {/* Mandatory Strategy Promotion Gate Visualizer */}
      <PromotionGateOverview currentActiveStage="DRAFT" />

      {/* Core Architectural Pillars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Capital-Safety Guarantees
            </h3>
            <Badge variant="success">Enforced Pre-Trade</Badge>
          </div>

          <ul className="space-y-3 text-xs text-slate-300">
            <li className="flex items-start gap-2.5">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                <strong className="text-white">Strict Idempotency:</strong> All order requests validated against an idempotency key before dispatch. Retried requests never duplicate live orders.
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                <strong className="text-white">Continuous Reconciliation:</strong> Internal position state verified against broker actuals on schedule and before every new order placement.
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                <strong className="text-white">Hard Stop Loss Limits:</strong> Synchronously evaluated before order placement. Breaching daily loss limit or max drawdown blocks new orders immediately.
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                <strong className="text-white">Staleness Protection:</strong> Orders fail-safe paused if market tick freshness exceeds 3000ms.
              </span>
            </li>
          </ul>
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FileCode2 className="w-4 h-4 text-primary" />
              Execution Sandbox & Security
            </h3>
            <Badge variant="default">Isolated Runtime</Badge>
          </div>

          <ul className="space-y-3 text-xs text-slate-300">
            <li className="flex items-start gap-2.5">
              <CheckCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <span>
                <strong className="text-white">AST Static Analysis:</strong> Prohibits <code className="bg-surface-raised px-1 py-0.5 rounded font-mono text-rose-400">eval()</code>, <code className="bg-surface-raised px-1 py-0.5 rounded font-mono text-rose-400">exec()</code>, <code className="bg-surface-raised px-1 py-0.5 rounded font-mono text-rose-400">open()</code>, and forbidden system/networking libraries.
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <span>
                <strong className="text-white">AI-Generated Code Review:</strong> AI drafts strategy code for human review and approval before entering the sandbox for backtesting.
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <span>
                <strong className="text-white">Broker Adapter Certification:</strong> All first-party and community broker adapters must pass sandbox validation before live capital routing.
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <span>
                <strong className="text-white">No Fast Path:</strong> Python, TradingView webhooks, MT5, Sheets, and AI strategies follow the identical 7-stage promotion lifecycle.
              </span>
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
};
