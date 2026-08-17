import React from "react";
import {
  FileCode,
  ShieldCheck,
  LineChart,
  GitBranch,
  FileSpreadsheet,
  UserCheck,
  Zap,
  ArrowRight,
  Lock,
} from "lucide-react";
import { StrategyPromotionStage } from "@/types";

interface StageConfig {
  id: StrategyPromotionStage;
  step: number;
  label: string;
  shortDesc: string;
  icon: React.ReactNode;
}

const STAGES: StageConfig[] = [
  {
    id: "DRAFT",
    step: 1,
    label: "Draft",
    shortDesc: "Strategy code or rules definition",
    icon: <FileCode className="w-5 h-5 text-slate-400" />,
  },
  {
    id: "SANDBOXED_CODE_REVIEW",
    step: 2,
    label: "Sandbox Review",
    shortDesc: "AST static analysis & capability linting",
    icon: <ShieldCheck className="w-5 h-5 text-cyan-400" />,
  },
  {
    id: "BACKTEST",
    step: 3,
    label: "Backtest",
    shortDesc: "Out-of-sample historical simulation",
    icon: <LineChart className="w-5 h-5 text-blue-400" />,
  },
  {
    id: "WALK_FORWARD_VALIDATION",
    step: 4,
    label: "Walk-Forward",
    shortDesc: "Out-of-sample parameter stability",
    icon: <GitBranch className="w-5 h-5 text-indigo-400" />,
  },
  {
    id: "PAPER_TRADING",
    step: 5,
    label: "Paper Trading",
    shortDesc: "14-day min live broker simulation",
    icon: <FileSpreadsheet className="w-5 h-5 text-amber-400" />,
  },
  {
    id: "HUMAN_APPROVAL",
    step: 6,
    label: "Human Approval",
    shortDesc: "Explicit trader sign-off on metrics",
    icon: <UserCheck className="w-5 h-5 text-emerald-400" />,
  },
  {
    id: "LIVE_TRADING",
    step: 7,
    label: "Live Trading",
    shortDesc: "Gradual capital scale & hard stops",
    icon: <Zap className="w-5 h-5 text-rose-400" />,
  },
];

interface PromotionGateOverviewProps {
  currentActiveStage?: StrategyPromotionStage;
}

export const PromotionGateOverview: React.FC<PromotionGateOverviewProps> = ({
  currentActiveStage = "DRAFT",
}) => {
  const currentIdx = STAGES.findIndex((s) => s.id === currentActiveStage);

  return (
    <div className="bg-surface border border-border rounded-xl p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/60 pb-4">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Lock className="w-4 h-4 text-primary" />
            Strategy Promotion Gate (Mandatory Lifecycle)
          </h2>
          <p className="text-xs text-slate-400">
            Uniform 7-stage promotion pipeline applying to all strategy sources (Python, AI, TradingView, MT5, Sheets). No fast paths.
          </p>
        </div>
        <div className="text-xs font-mono px-2.5 py-1 bg-surface-raised rounded text-slate-300 border border-border">
          Live Disabled by Default
        </div>
      </div>

      {/* Visual Pipeline */}
      <div className="grid grid-cols-1 md:grid-cols-7 gap-3 pt-2">
        {STAGES.map((stage, idx) => {
          const isPassed = idx < currentIdx;
          const isCurrent = idx === currentIdx;

          return (
            <div key={stage.id} className="relative flex flex-col items-center">
              <div
                className={`w-full h-full flex flex-col p-3 rounded-lg border transition-all ${
                  isCurrent
                    ? "bg-primary/10 border-primary shadow-md shadow-primary/10"
                    : isPassed
                    ? "bg-surface-raised/80 border-emerald-500/40 text-slate-300"
                    : "bg-surface-raised/30 border-border/60 text-slate-500"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                      isCurrent
                        ? "bg-primary text-white"
                        : isPassed
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-surface text-slate-500"
                    }`}
                  >
                    Step {stage.step}
                  </span>
                  {stage.icon}
                </div>

                <div className="font-semibold text-xs text-slate-200 mt-1">
                  {stage.label}
                </div>
                <div className="text-[11px] text-slate-400 mt-1 leading-tight">
                  {stage.shortDesc}
                </div>
              </div>

              {idx < STAGES.length - 1 && (
                <div className="hidden md:block absolute -right-2.5 top-1/2 -translate-y-1/2 z-10 text-slate-600">
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
