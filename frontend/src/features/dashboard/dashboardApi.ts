import { apiClient } from "@/api/client";
import { ApiSuccessResponse } from "@/types/api";

export interface DashboardOverviewDTO {
  total_dealers: number;
  total_confirmation_links: number;
  links_shared: number;
  regenerated_links: number;
  confirmations_received: number;
  pending_confirmations: number;
  expired_links: number;
  todays_confirmations: number;
  upcoming_bookings: number;
}

export interface DashboardAnalyticsDTO {
  daily_confirmations: Array<{ date: string; count: number }>;
  monthly_confirmations: Array<{ month: string; count: number }>;
  rm_performance: Array<{
    rm_id: string;
    rm_name: string;
    total_links: number;
    shared_links: number;
    regenerated_links: number;
    confirmed: number;
    pending: number;
    expired: number;
    conversion_rate: number;
  }>;
  campaign_performance: Array<{
    campaign_id: string;
    campaign_name: string;
    total_links: number;
    confirmed: number;
    pending: number;
    conversion_rate: number;
  }>;
  date_wise_bookings: Array<{ date: string; count: number }>;
  time_slot_utilization: Array<{
    slot_id: string;
    label: string;
    booked: number;
    max_capacity: number;
  }>;
  pending_vs_confirmed: {
    confirmed: number;
    pending: number;
    expired: number;
  };
}

export const dashboardApi = {
  async overview(params?: Record<string, string>): Promise<DashboardOverviewDTO> {
    const { data } = await apiClient.get<ApiSuccessResponse<DashboardOverviewDTO>>(
      "/dashboard/overview/",
      { params }
    );
    return data.data;
  },

  async analytics(params?: Record<string, string>): Promise<DashboardAnalyticsDTO> {
    const { data } = await apiClient.get<ApiSuccessResponse<DashboardAnalyticsDTO>>(
      "/dashboard/analytics/",
      { params }
    );
    return data.data;
  },
};
