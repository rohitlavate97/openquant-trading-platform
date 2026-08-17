import React, { useState } from "react";
import { Key, Plus, Trash2, Copy, Check, ShieldAlert } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { APIKeySummary, Permission } from "@/types/auth";

export const APIKeyManagement: React.FC = () => {
  const [keys, setKeys] = useState<APIKeySummary[]>([
    {
      key_id: "key_demo_algo",
      name: "Algorithmic Trigger Engine",
      prefix: "oq_live_4a91",
      permissions: ["ORDER_MANAGE", "READ_ONLY"],
      is_active: true,
      last_used_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
    },
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [keyName, setKeyName] = useState("");
  const [selectedPerms, setSelectedPerms] = useState<Permission[]>(["READ_ONLY"]);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName) return;

    const rawKey = `oq_live_${Math.random().toString(36).substring(2)}${Math.random().toString(36).substring(2)}`;
    const newSummary: APIKeySummary = {
      key_id: `key_${Date.now()}`,
      name: keyName,
      prefix: rawKey.slice(0, 12),
      permissions: selectedPerms,
      is_active: true,
      last_used_at: null,
      created_at: new Date().toISOString(),
    };

    setKeys((prev) => [...prev, newSummary]);
    setNewlyCreatedKey(rawKey);
    setKeyName("");
  };

  const handleCopy = () => {
    if (newlyCreatedKey) {
      navigator.clipboard.writeText(newlyCreatedKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRevoke = (keyId: string) => {
    setKeys((prev) => prev.filter((k) => k.key_id !== keyId));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Key className="w-5 h-5 text-primary" />
            Programmatic API Keys
          </h2>
          <p className="text-xs text-slate-400">
            Generate and manage high-entropy keys for external order dispatch, TradingView webhooks, and REST automation.
          </p>
        </div>

        <Button size="sm" onClick={() => { setIsModalOpen(true); setNewlyCreatedKey(null); }}>
          <Plus className="w-4 h-4 mr-1.5" />
          Create API Key
        </Button>
      </div>

      {/* Keys List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {keys.map((k) => (
          <Card key={k.key_id} className="space-y-3">
            <div className="flex items-center justify-between border-b border-border/60 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-primary/20 text-primary rounded-lg">
                  <Key className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white">{k.name}</div>
                  <div className="text-[11px] text-slate-400 font-mono">
                    Prefix: {k.prefix}••••••••
                  </div>
                </div>
              </div>
              <Badge variant="success" className="text-[10px]">Active</Badge>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-1">
              {k.permissions.map((p) => (
                <Badge key={p} variant="default" className="text-[10px] font-mono">
                  {p}
                </Badge>
              ))}
            </div>

            <div className="flex items-center justify-between pt-2 text-[10px] text-slate-500 font-mono border-t border-border/40">
              <span>Created {new Date(k.created_at).toLocaleDateString()}</span>
              <button
                type="button"
                onClick={() => handleRevoke(k.key_id)}
                className="text-rose-400 hover:text-rose-300 flex items-center gap-1 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Revoke Key
              </button>
            </div>
          </Card>
        ))}
      </div>

      {/* Create Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-surface border border-border rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Generate Programmatic API Key</h3>

            {newlyCreatedKey ? (
              <div className="space-y-4">
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-start gap-2.5">
                  <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-200">
                    Make sure to copy your API key now. You won't be able to see it again!
                  </p>
                </div>

                <div className="p-3 bg-surface-raised border border-border rounded-lg flex items-center justify-between font-mono text-xs text-slate-200">
                  <span className="truncate mr-2">{newlyCreatedKey}</span>
                  <button
                    type="button"
                    onClick={handleCopy}
                    className="p-1.5 hover:bg-surface rounded text-primary hover:text-primary-hover"
                  >
                    {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>

                <div className="flex justify-end pt-2">
                  <Button size="sm" onClick={() => setIsModalOpen(false)}>
                    Done
                  </Button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleCreate} className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Key Description / Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. TradingView Webhook Key"
                    value={keyName}
                    onChange={(e) => setKeyName(e.target.value)}
                    className="w-full bg-surface-raised border border-border rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-2">Granular Scoped Permissions</label>
                  <div className="space-y-2">
                    {(["READ_ONLY", "ORDER_MANAGE", "STRATEGY_CREATE", "KILL_SWITCH_TRIGGER"] as Permission[]).map(
                      (p) => (
                        <label key={p} className="flex items-center gap-2 cursor-pointer text-slate-300">
                          <input
                            type="checkbox"
                            checked={selectedPerms.includes(p)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedPerms((prev) => [...prev, p]);
                              } else {
                                setSelectedPerms((prev) => prev.filter((item) => item !== p));
                              }
                            }}
                            className="rounded border-slate-700 text-primary focus:ring-primary"
                          />
                          <span className="font-mono text-[11px]">{p}</span>
                        </label>
                      )
                    )}
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-3">
                  <Button variant="ghost" size="sm" type="button" onClick={() => setIsModalOpen(false)}>
                    Cancel
                  </Button>
                  <Button variant="primary" size="sm" type="submit">
                    Generate Secret Key
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
