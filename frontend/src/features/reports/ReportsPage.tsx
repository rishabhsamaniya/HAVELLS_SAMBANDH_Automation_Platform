import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileSpreadsheet, FileText } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { PermissionGate } from "@/components/ui/PermissionGate";
import { REPORT_TABS, reportsApi } from "./reportsApi";

export const ReportsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<(typeof REPORT_TABS)[number]>(REPORT_TABS[0]);
  const [dealerCode, setDealerCode] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const params: Record<string, string> = {
    ...(dealerCode ? { dealer_code: dealerCode } : {}),
    ...(startDate ? { start_date: startDate } : {}),
    ...(endDate ? { end_date: endDate } : {}),
  };

  const { data, isLoading } = useQuery({
    queryKey: ["report", activeTab.slug, dealerCode, startDate, endDate],
    queryFn: () => reportsApi.fetchReport(activeTab.slug, params),
  });

  const handleExport = async (format: "xlsx" | "csv") => {
    const blob = await reportsApi.exportReport(activeTab.key, format, params);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `havells_${activeTab.key}_report.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-primary">Reports &amp; Exports</h1>
          <p className="text-xs text-ink-secondary mt-1">
            Generate permission-scoped operational and analytical reports in Excel or CSV format.
          </p>
        </div>
        <PermissionGate permission="reports.export">
          <div className="flex gap-2">
            <Button variant="secondary" size="md" leftIcon={<FileText className="h-4 w-4" />} onClick={() => handleExport("csv")}>
              Export CSV
            </Button>
            <Button size="md" leftIcon={<FileSpreadsheet className="h-4 w-4" />} onClick={() => handleExport("xlsx")}>
              Export Excel
            </Button>
          </div>
        </PermissionGate>
      </div>

      {/* Report Tabs */}
      <div className="flex flex-wrap gap-2">
        {REPORT_TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={[
              "px-3.5 py-2 rounded-lg text-xs font-medium transition-colors",
              activeTab.key === tab.key
                ? "bg-brand-primary text-white"
                : "bg-surface-white border border-line text-ink-primary hover:bg-surface-muted",
            ].join(" ")}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filter Bar */}
      <div className="bg-surface-white border border-line rounded-xl p-4 shadow-card flex flex-wrap gap-3">
        <input
          type="text"
          value={dealerCode}
          onChange={(e) => setDealerCode(e.target.value)}
          placeholder="Filter Dealer Code..."
          className="h-[38px] px-3 text-xs rounded-lg border border-line"
        />
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="h-[38px] px-3 text-xs rounded-lg border border-line"
        />
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="h-[38px] px-3 text-xs rounded-lg border border-line"
        />
      </div>

      {/* Preview Table */}
      <div className="bg-surface-white border border-line rounded-xl shadow-card overflow-hidden">
        <div className="px-4 py-3 border-b border-line flex items-center justify-between">
          <h2 className="text-sm font-semibold text-ink-primary">{data?.title || activeTab.label}</h2>
          <span className="text-xs text-ink-secondary tabular-nums">{data?.total ?? 0} record(s)</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-bg border-b border-line text-xs font-semibold uppercase tracking-wider text-ink-secondary">
                {(data?.headers || []).map((h) => (
                  <th key={h} className="py-3 px-4 whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-line text-sm">
              {isLoading ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-ink-secondary">
                    Loading report...
                  </td>
                </tr>
              ) : !data || data.rows.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-ink-secondary">
                    No records match the selected filters.
                  </td>
                </tr>
              ) : (
                data.rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-surface-bg/60">
                    {data.headers.map((h) => (
                      <td key={h} className="py-3 px-4 whitespace-nowrap tabular-nums">
                        {String(row[h] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
