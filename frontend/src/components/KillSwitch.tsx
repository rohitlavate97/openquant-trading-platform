import React, { useState } from "react";
import { AlertOctagon, ShieldAlert, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/Button";

interface KillSwitchProps {
  isActive: boolean;
  onToggle: (activate: boolean, flattenPositions: boolean) => void;
}

export const KillSwitch: React.FC<KillSwitchProps> = ({ isActive, onToggle }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [flattenPositions, setFlattenPositions] = useState(false);

  const handleConfirm = () => {
    onToggle(!isActive, flattenPositions);
    setIsOpen(false);
  };

  return (
    <>
      <button
        type="button"
        id="global-kill-switch-btn"
        onClick={() => setIsOpen(true)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-semibold text-xs transition-all border ${
          isActive
            ? "bg-danger text-white border-rose-500 animate-pulse shadow-lg shadow-rose-950/50"
            : "bg-surface-raised hover:bg-danger/20 text-rose-400 border-rose-500/40 hover:border-rose-500"
        }`}
        title="Global Emergency Kill Switch — 1-click order halting"
      >
        <AlertOctagon className="w-4 h-4 text-current" />
        <span>{isActive ? "KILL SWITCH ACTIVE" : "EMERGENCY KILL SWITCH"}</span>
      </button>

      {/* Confirmation Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-surface border border-rose-500/50 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-danger/20 rounded-xl text-danger">
                <ShieldAlert className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">
                  {isActive ? "Deactivate Kill Switch?" : "ACTIVATE GLOBAL KILL SWITCH?"}
                </h3>
                <p className="text-xs text-slate-400">Pre-trade capital protection protocol</p>
              </div>
            </div>

            <p className="text-sm text-slate-300">
              {isActive
                ? "Resuming order placement will allow strategies in authorized states to submit orders once again. Confirm this action."
                : "Activating the Kill Switch will IMMEDIATELY block all inbound order placement across all strategies, accounts, and brokers synchronously."}
            </p>

            {!isActive && (
              <label className="flex items-center gap-3 p-3 bg-surface-raised rounded-lg cursor-pointer border border-border">
                <input
                  type="checkbox"
                  checked={flattenPositions}
                  onChange={(e) => setFlattenPositions(e.target.checked)}
                  className="rounded border-slate-700 text-danger focus:ring-danger w-4 h-4"
                />
                <span className="text-xs text-slate-200 font-medium">
                  Simultaneously flatten (close) all open positions across accounts
                </span>
              </label>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button
                variant={isActive ? "primary" : "danger"}
                size="sm"
                onClick={handleConfirm}
                id="confirm-kill-switch-action"
              >
                {isActive ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-1.5" />
                    Resume Order Placement
                  </>
                ) : (
                  <>
                    <AlertOctagon className="w-4 h-4 mr-1.5" />
                    Confirm Emergency Halt
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
