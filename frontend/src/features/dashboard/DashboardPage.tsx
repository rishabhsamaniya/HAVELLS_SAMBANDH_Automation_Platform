import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Building2,
  Link2,
  Share2,
  CheckCircle2,
  Clock,
  AlertTriangle,
  CalendarCheck,
  CalendarDays,
  RefreshCw,
  PauseCircle,
  CalendarClock,
  ClipboardCheck,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

import { KPICard } from "@/components/ui/KPICard";
import { dashboardApi } from "./dashboardApi";

const PIE_COLORS = ["#16A34A", "#F59E0B", "#DC2626"];

export const DashboardPage: React.FC = () => {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const params: Record<string, string> = {
    ...(startDate ? { start_date: startDate } : {}),
    ...(endDate ? { end_date: endDate } : {}),
  };

  const { data: overview } = useQuery({
    queryKey: ["dashboard-overview", startDate, endDate],
    queryFn: () => dashboardApi.overview(params),
    refetchOnMount: "always",
  });

  const { data: analytics } = useQuery({
    queryKey: ["dashboard-analytics", startDate, endDate],
    queryFn: () => dashboardApi.analytics(params),
    refetchOnMount: "always",
  });

  const pieData = analytics
    ? [
        { name: "Confirmed", value: analytics.pending_vs_confirmed.confirmed },
        { name: "Pending", value: analytics.pending_vs_confirmed.pending },
        { name: "Expired", value: analytics.pending_vs_confirmed.expired },
      ]
    : [];

  const actionChartData = [
    { name: "Completed", count: overview?.experience_completed ?? 0, fill: "#16A34A" },
    { name: "On Hold", count: overview?.experience_on_hold ?? 0, fill: "#F59E0B" },
    { name: "Postponed", count: overview?.experience_postponed ?? 0, fill: "#2563EB" },
    { name: "Pending Action", count: overview?.action_pending ?? 0, fill: "#6B7280" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-primary">Dashboard</h1>
          <p className="text-xs text-ink-secondary mt-1">
            Real-time dealer outreach, confirmation progress, and slot utilization.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            aria-label="Start date"
            className="h-[38px] px-3 text-xs rounded-lg border border-line bg-surface-white"
          />
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            aria-label="End date"
            className="h-[38px] px-3 text-xs rounded-lg border border-line bg-surface-white"
          />
        </div>
      </div>

      {/* Executive KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <KPICard label="Total Dealers" value={overview?.total_dealers ?? "—"} icon={<Building2 className="h-5 w-5" />} />
        <KPICard label="Total Confirmation Links" value={overview?.total_confirmation_links ?? "—"} icon={<Link2 className="h-5 w-5" />} />
        <KPICard label="Links Shared" value={overview?.links_shared ?? "—"} icon={<Share2 className="h-5 w-5" />} />
        <KPICard label="Regenerated Links" value={overview?.regenerated_links ?? "—"} icon={<RefreshCw className="h-5 w-5" />} />
        <KPICard label="Confirmations Received" value={overview?.confirmations_received ?? "—"} icon={<CheckCircle2 className="h-5 w-5" />} />
        <KPICard label="Pending Confirmations" value={overview?.pending_confirmations ?? "—"} icon={<Clock className="h-5 w-5" />} />
        <KPICard label="Expired Links" value={overview?.expired_links ?? "—"} icon={<AlertTriangle className="h-5 w-5" />} />
        <KPICard label="Today's Confirmations" value={overview?.todays_confirmations ?? "—"} icon={<CalendarCheck className="h-5 w-5" />} />
        <KPICard label="Upcoming Bookings" value={overview?.upcoming_bookings ?? "—"} icon={<CalendarDays className="h-5 w-5" />} />
        <KPICard label="Experience Completed" value={overview?.experience_completed ?? 0} icon={<ClipboardCheck className="h-5 w-5 text-[#15803D]" />} />
        <KPICard label="Experience on Hold" value={overview?.experience_on_hold ?? 0} icon={<PauseCircle className="h-5 w-5 text-[#B45309]" />} />
        <KPICard label="Experience Postponed" value={overview?.experience_postponed ?? 0} icon={<CalendarClock className="h-5 w-5 text-[#1D4ED8]" />} />
      </div>

      {/* Action-Wise Summary */}
      <div className="bg-surface-white border border-line rounded-xl shadow-card overflow-hidden">
        <div className="px-5 py-4 border-b border-line flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold text-ink-primary">Action-Wise Experience Summary</h2>
            <p className="text-xs text-ink-secondary mt-0.5">
              Live breakdown of Experience Completed, On Hold, and Postponed bookings with reason-wise remarks.
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-surface-bg text-ink-secondary border border-line">
            <Clock className="h-3.5 w-3.5" />
            Action Pending: <strong className="text-ink-primary tabular-nums">{overview?.action_pending ?? 0}</strong>
          </span>
        </div>

        <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-4">
          {(
            analytics?.action_summary || [
              { action: "experience_completed" as const, label: "Experience Completed", count: overview?.experience_completed ?? 0, percentage: 0, remarks_breakdown: [] },
              { action: "experience_on_hold" as const, label: "Experience on Hold", count: overview?.experience_on_hold ?? 0, percentage: 0, remarks_breakdown: [] },
              { action: "experience_postponed" as const, label: "Experience Postponed", count: overview?.experience_postponed ?? 0, percentage: 0, remarks_breakdown: [] },
            ]
          ).map((item) => {
            const styleMap = {
              experience_completed: {
                card: "border-[#BBF7D0] bg-[#F0FDF4]/60",
                badge: "bg-[#DCFCE7] text-[#15803D]",
                bar: "bg-[#16A34A]",
                icon: <ClipboardCheck className="h-5 w-5 text-[#15803D]" />,
              },
              experience_on_hold: {
                card: "border-[#FDE68A] bg-[#FFFBEB]/60",
                badge: "bg-[#FEF3C7] text-[#B45309]",
                bar: "bg-[#F59E0B]",
                icon: <PauseCircle className="h-5 w-5 text-[#B45309]" />,
              },
              experience_postponed: {
                card: "border-[#BFDBFE] bg-[#EFF6FF]/60",
                badge: "bg-[#DBEAFE] text-[#1D4ED8]",
                bar: "bg-[#2563EB]",
                icon: <CalendarClock className="h-5 w-5 text-[#1D4ED8]" />,
              },
            }[item.action];

            return (
              <div key={item.action} className={`rounded-xl border p-4 space-y-3 ${styleMap.card}`}>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-ink-secondary">
                      {item.label}
                    </p>
                    <div className="flex items-baseline gap-2 mt-1">
                      <span className="text-2xl font-bold text-ink-primary tabular-nums">
                        {item.count}
                      </span>
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full tabular-nums ${styleMap.badge}`}>
                        {item.percentage}%
                      </span>
                    </div>
                  </div>
                  <div className="h-9 w-9 rounded-lg bg-surface-white border border-line/60 flex items-center justify-center shrink-0">
                    {styleMap.icon}
                  </div>
                </div>

                <div className="w-full h-1.5 rounded-full bg-surface-white overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${styleMap.bar}`}
                    style={{ width: `${Math.min(100, item.percentage)}%` }}
                  />
                </div>

                <div className="pt-1 border-t border-line/50 space-y-1.5">
                  <p className="text-[11px] font-semibold text-ink-secondary uppercase tracking-wider">
                    Remarks Breakdown
                  </p>
                  {item.remarks_breakdown.length > 0 ? (
                    <ul className="space-y-1">
                      {item.remarks_breakdown.map((r) => (
                        <li key={r.remark} className="flex items-start justify-between gap-2 text-xs text-ink-primary">
                          <span className="leading-snug">{r.remark}</span>
                          <span className="font-semibold tabular-nums shrink-0 px-1.5 py-0.5 rounded bg-surface-white border border-line text-[11px]">
                            {r.count}
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-ink-secondary">No remarks recorded yet.</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-surface-white border border-line rounded-xl p-5 shadow-card">
          <h2 className="text-base font-semibold text-ink-primary mb-4">Action-Wise Summary</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={actionChartData}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {actionChartData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-surface-white border border-line rounded-xl p-5 shadow-card">
          <h2 className="text-base font-semibold text-ink-primary mb-4">Daily Confirmations</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics?.daily_confirmations || []}>
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#D71920" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-surface-white border border-line rounded-xl p-5 shadow-card">
          <h2 className="text-base font-semibold text-ink-primary mb-4">Confirmed vs Pending vs Expired</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={85}>
                  {pieData.map((_, idx) => (
                    <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* RM-wise Performance */}
      <div className="bg-surface-white border border-line rounded-xl shadow-card overflow-hidden">
        <div className="px-5 py-4 border-b border-line">
          <h2 className="text-base font-semibold text-ink-primary">RM-Wise Performance</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-bg border-b border-line text-xs font-semibold uppercase tracking-wider text-ink-secondary">
                <th className="py-3 px-4">RM Name</th>
                <th className="py-3 px-4">Links</th>
                <th className="py-3 px-4">Shared</th>
                <th className="py-3 px-4">Regenerated</th>
                <th className="py-3 px-4">Confirmed</th>
                <th className="py-3 px-4">Completed</th>
                <th className="py-3 px-4">On Hold</th>
                <th className="py-3 px-4">Postponed</th>
                <th className="py-3 px-4">Pending</th>
                <th className="py-3 px-4">Conversion</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line text-sm">
              {(analytics?.rm_performance || []).map((row) => (
                <tr key={row.rm_id}>
                  <td className="py-3 px-4 font-medium">{row.rm_name}</td>
                  <td className="py-3 px-4 tabular-nums">{row.total_links}</td>
                  <td className="py-3 px-4 tabular-nums">{row.shared_links}</td>
                  <td className="py-3 px-4 tabular-nums">{row.regenerated_links}</td>
                  <td className="py-3 px-4 tabular-nums text-status-success font-semibold">{row.confirmed}</td>
                  <td className="py-3 px-4 tabular-nums text-[#15803D] font-medium">{row.experience_completed ?? 0}</td>
                  <td className="py-3 px-4 tabular-nums text-[#B45309] font-medium">{row.experience_on_hold ?? 0}</td>
                  <td className="py-3 px-4 tabular-nums text-[#1D4ED8] font-medium">{row.experience_postponed ?? 0}</td>
                  <td className="py-3 px-4 tabular-nums text-status-warning">{row.pending}</td>
                  <td className="py-3 px-4 tabular-nums">{row.conversion_rate}%</td>
                </tr>
              ))}
              {(!analytics?.rm_performance || analytics.rm_performance.length === 0) && (
                <tr>
                  <td colSpan={10} className="py-6 text-center text-ink-secondary">
                    No RM performance data available yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
