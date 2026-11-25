import { apiClient } from "@/api/client";
import { ApiSuccessResponse } from "@/types/api";

export interface ReportPayload {
  report: string;
  title: string;
  headers: string[];
  total: number;
  rows: Array<Record<string, string | number>>;
}

export const REPORT_TABS = [
  { key: "confirmations", slug: "confirmations", label: "Confirmation Report" },
  { key: "pending", slug: "pending", label: "Pending Dealers" },
  { key: "dealer_master", slug: "dealer-master", label: "Dealer Master" },
  { key: "rm_performance", slug: "rm-performance", label: "RM-Wise" },
  { key: "campaign_wise", slug: "campaign-wise", label: "Campaign-Wise" },
  { key: "date_wise", slug: "date-wise", label: "Date-Wise" },
  { key: "time_slot", slug: "time-slot", label: "Time-Slot" },
  { key: "link_usage", slug: "link-usage", label: "Link Usage" },
] as const;

export const reportsApi = {
  async fetchReport(slug: string, params?: Record<string, string>): Promise<ReportPayload> {
    const { data } = await apiClient.get<ApiSuccessResponse<ReportPayload>>(`/reports/${slug}/`, {
      params,
    });
    return data.data;
  },

  async exportReport(reportKey: string, format: "xlsx" | "csv", params?: Record<string, string>): Promise<Blob> {
    const { data } = await apiClient.get("/reports/export/", {
      params: { report: reportKey, format, ...params },
      responseType: "blob",
    });
    return data;
  },
};
