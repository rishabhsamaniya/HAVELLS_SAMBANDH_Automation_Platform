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
  });

  const { data: analytics } = useQuery({
    queryKey: ["dashboard-analytics", startDate, endDate],
    queryFn: () => dashboardApi.analytics(params),
  });

  const pieData = analytics
    ? [
        { name: "Confirmed", value: analytics.pending_vs_confirmed.confirmed },
        { name: "Pending", value: analytics.pending_vs_confirmed.pending },
        { name: "Expired", value: analytics.pending_vs_confirmed.expired },
      ]
    : [];

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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        <KPICard label="Total Dealers" value={overview?.total_dealers ?? "—"} icon={<Building2 className="h-5 w-5" />} />
        <KPICard label="Total Confirmation Links" value={overview?.total_confirmation_links ?? "—"} icon={<Link2 className="h-5 w-5" />} />
        <KPICard label="Links Shared" value={overview?.links_shared ?? "—"} icon={<Share2 className="h-5 w-5" />} />
        <KPICard label="Regenerated Links" value={overview?.regenerated_links ?? "—"} icon={<RefreshCw className="h-5 w-5" />} />
        <KPICard label="Confirmations Received" value={overview?.confirmations_received ?? "—"} icon={<CheckCircle2 className="h-5 w-5" />} />
        <KPICard label="Pending Confirmations" value={overview?.pending_confirmations ?? "—"} icon={<Clock className="h-5 w-5" />} />
        <KPICard label="Expired Links" value={overview?.expired_links ?? "—"} icon={<AlertTriangle className="h-5 w-5" />} />
        <KPICard label="Today's Confirmations" value={overview?.todays_confirmations ?? "—"} icon={<CalendarCheck className="h-5 w-5" />} />
        <KPICard label="Upcoming Bookings" value={overview?.upcoming_bookings ?? "—"} icon={<CalendarDays className="h-5 w-5" />} />
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
                  <td className="py-3 px-4 tabular-nums text-status-warning">{row.pending}</td>
                  <td className="py-3 px-4 tabular-nums">{row.conversion_rate}%</td>
                </tr>
              ))}
              {(!analytics?.rm_performance || analytics.rm_performance.length === 0) && (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-ink-secondary">
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
