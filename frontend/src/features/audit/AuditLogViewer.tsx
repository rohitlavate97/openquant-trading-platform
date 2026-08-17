import React, { useState } from "react";
import {
  FileText,
  ShieldAlert,
  AlertTriangle,
  Info,
  Filter,
  Search,
  Eye,
  X,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export interface AuditLogEntry {
  log_id: string;
  timestamp: string;
  event_type: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  actor_id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  payload: Record<string, any>;
  status: "SUCCESS" | "BLOCKED" | "FAILURE";
  reason?: string | null;
}

const DEMO_LOGS: AuditLogEntry[] = [
  {
    log_id: "aud_01_ks",
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    event_type: "KILL_SWITCH_STATUS",
    severity: "CRITICAL",
    actor_id: "usr_admin_01",
    entity_type: "SYSTEM",
    entity_id: "GLOBAL",
    action: "HEALTH_CHECK",
    payload: { state: "READY", fail_safe_enabled: true },
    status: "SUCCESS",
  },
  {
    log_id: "aud_02_sec",
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    event_type: "BROKER_CREDENTIALS_STORED",
    severity: "INFO",
    actor_id: "usr_admin_01",
    entity_type: "BROKER_CREDENTIAL",
    entity_id: "zerodha",
    action: "ENCRYPT_AND_PERSIST",
    payload: { broker_id: "zerodha", key_version: 1, encryption: "AES-128-CBC+HMAC-SHA256" },
    status: "SUCCESS",
  },
  {
    log_id: "aud_03_ast",
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    event_type: "SANDBOX_AST_ANALYSIS",
    severity: "INFO",
    actor_id: "usr_quant_02",
    entity_type: "STRATEGY",
    entity_id: "strat_stat_arb_01",
    action: "VALIDATE_CODE",
    payload: { violations_found: 0, is_safe: true, modules_scanned: ["math", "decimal"] },
    status: "SUCCESS",
  },
  {
    log_id: "aud_04_auth",
    timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    event_type: "USER_LOGIN_SUCCESS",
    severity: "INFO",
    actor_id: "usr_admin_01",
    entity_type: "USER",
    entity_id: "usr_admin_01",
    action: "JWT_TOKEN_ISSUED",
    payload: { role: "ADMIN", auth_method: "password_bcrypt" },
    status: "SUCCESS",
  },
];

export const AuditLogViewer: React.FC = () => {
  const [logs] = useState<AuditLogEntry[]>(DEMO_LOGS);
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedPayload, setSelectedPayload] = useState<AuditLogEntry | null>(null);

  const filteredLogs = logs.filter((log) => {
    if (severityFilter !== "ALL" && log.severity !== severityFilter) {
      return false;
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        log.event_type.toLowerCase().includes(q) ||
        log.actor_id.toLowerCase().includes(q) ||
        log.action.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "CRITICAL":
        return (
          <Badge variant="danger" className="flex items-center gap-1 font-mono text-[10px]">
            <ShieldAlert className="w-3 h-3" />
            CRITICAL
          </Badge>
        );
      case "WARNING":
        return (
          <Badge variant="warning" className="flex items-center gap-1 font-mono text-[10px]">
            <AlertTriangle className="w-3 h-3" />
            WARNING
          </Badge>
        );
      case "INFO":
      default:
        return (
          <Badge variant="default" className="flex items-center gap-1 font-mono text-[10px] text-blue-400 border-blue-500/30">
            <Info className="w-3 h-3" />
            INFO
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary" />
            Immutable Audit Trail & Compliance Logs
          </h2>
          <p className="text-xs text-slate-400">
            Cryptographically structured, append-only log capturing risk actions, promotions, kill switch triggers, and credential access.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-xs text-slate-300">
            Append-Only Active
          </Badge>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search event type, actor..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-surface-raised border border-border rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-primary font-mono"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs text-slate-400">Severity:</span>
          {["ALL", "CRITICAL", "WARNING", "INFO"].map((sev) => (
            <button
              key={sev}
              type="button"
              onClick={() => setSeverityFilter(sev)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                severityFilter === sev
                  ? "bg-primary text-white font-semibold"
                  : "bg-surface-raised text-slate-400 hover:text-slate-200"
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </Card>

      {/* Log Table */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-surface-raised/80 text-slate-400 uppercase font-mono text-[10px] border-b border-border">
              <tr>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Entity</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4 text-right">Payload</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 font-mono">
              {filteredLogs.map((log) => (
                <tr key={log.log_id} className="hover:bg-surface-raised/40 transition-colors">
                  <td className="py-3 px-4 text-slate-400 whitespace-nowrap text-[11px]">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="py-3 px-4">{getSeverityBadge(log.severity)}</td>
                  <td className="py-3 px-4 font-semibold text-slate-200">{log.event_type}</td>
                  <td className="py-3 px-4 text-slate-400">{log.actor_id}</td>
                  <td className="py-3 px-4 text-slate-300">
                    {log.entity_type} <span className="text-slate-500">({log.entity_id})</span>
                  </td>
                  <td className="py-3 px-4 text-slate-400">{log.action}</td>
                  <td className="py-3 px-4 text-right">
                    <button
                      type="button"
                      onClick={() => setSelectedPayload(log)}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-surface-raised hover:bg-surface text-primary hover:text-primary-hover rounded border border-border/80 text-[10px] transition-colors"
                    >
                      <Eye className="w-3 h-3" />
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* JSON Payload Inspector Modal */}
      {selectedPayload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-surface border border-border rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border/60 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <FileText className="w-4 h-4 text-primary" />
                  Audit Log Details
                </h3>
                <p className="text-[11px] font-mono text-slate-400">{selectedPayload.log_id}</p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedPayload(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Event:</span>
                <span className="font-semibold text-white font-mono">{selectedPayload.event_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Actor:</span>
                <span className="text-slate-200 font-mono">{selectedPayload.actor_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Timestamp:</span>
                <span className="text-slate-200 font-mono">{selectedPayload.timestamp}</span>
              </div>
            </div>

            <div>
              <label className="block text-slate-400 text-xs font-semibold mb-1">Structured JSON Payload</label>
              <pre className="p-3 bg-background border border-border rounded-lg text-[11px] font-mono text-emerald-400 overflow-x-auto max-h-60">
                {JSON.stringify(selectedPayload.payload, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end pt-2">
              <Button size="sm" variant="secondary" onClick={() => setSelectedPayload(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
