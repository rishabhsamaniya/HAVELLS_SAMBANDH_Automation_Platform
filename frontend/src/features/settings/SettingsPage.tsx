import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/features/auth/AuthContext";
import { Button } from "@/components/ui/Button";
import { PermissionGate } from "@/components/ui/PermissionGate";
import { auditLogsApi } from "./auditLogsApi";

export const SettingsPage: React.FC = () => {
  const { user, hasPermission } = useAuth();
  const [tab, setTab] = useState<"profile" | "audit">("profile");

  const { data: logs = [] } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => auditLogsApi.list(),
    enabled: tab === "audit" && hasPermission("audit_logs.view"),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink-primary">Profile &amp; Settings</h1>
        <p className="text-xs text-ink-secondary mt-1">
          Manage your account details and review immutable system audit trails.
        </p>
      </div>

      <div className="flex gap-2 border-b border-line pb-2">
        <Button variant={tab === "profile" ? "primary" : "ghost"} size="sm" onClick={() => setTab("profile")}>
          My Profile
        </Button>
        <PermissionGate permission="audit_logs.view">
          <Button variant={tab === "audit" ? "primary" : "ghost"} size="sm" onClick={() => setTab("audit")}>
            Audit Logs
          </Button>
        </PermissionGate>
      </div>

      {tab === "profile" ? (
        <div className="bg-surface-white border border-line rounded-xl p-6 shadow-card max-w-xl space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-ink-secondary">Full Name</p>
              <p className="font-semibold text-ink-primary mt-0.5">{user?.full_name}</p>
            </div>
            <div>
              <p className="text-xs text-ink-secondary">Mobile Number</p>
              <p className="font-semibold text-ink-primary tabular-nums mt-0.5">+91 {user?.mobile_number}</p>
            </div>
            <div>
              <p className="text-xs text-ink-secondary">Email</p>
              <p className="font-medium text-ink-primary mt-0.5">{user?.email || "—"}</p>
            </div>
            <div>
              <p className="text-xs text-ink-secondary">Assigned Role(s)</p>
              <p className="font-medium text-ink-primary mt-0.5">
                {user?.roles?.map((r) => r.name).join(", ") || (user?.is_superuser ? "Super Admin" : "—")}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-surface-white border border-line rounded-xl shadow-card overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-bg border-b border-line text-xs font-semibold uppercase tracking-wider text-ink-secondary">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Module</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Object</th>
                <th className="py-3 px-4">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line text-xs">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-surface-bg/60">
                  <td className="py-3 px-4 tabular-nums whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString("en-IN")}
                  </td>
                  <td className="py-3 px-4 font-medium">{log.user_name}</td>
                  <td className="py-3 px-4">{log.module}</td>
                  <td className="py-3 px-4 font-semibold text-ink-primary">{log.action}</td>
                  <td className="py-3 px-4 tabular-nums">
                    {log.object_type} {log.object_id ? `(${log.object_id.slice(0, 8)}...)` : ""}
                  </td>
                  <td className="py-3 px-4 tabular-nums">{log.ip_address || "—"}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-ink-secondary">
                    No audit events recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
