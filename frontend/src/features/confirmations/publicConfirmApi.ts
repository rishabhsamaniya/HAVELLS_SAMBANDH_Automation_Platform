import axios from "axios";
import { ApiSuccessResponse } from "@/types/api";

const publicClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  headers: { "Content-Type": "application/json" },
});

export interface PublicLinkMetadata {
  campaign_name: string;
  allowed_month: string;
  timezone: string;
  expires_at: string;
  available_dates: string[];
  has_available_dates: boolean;
}

export interface AvailableSlotDTO {
  id: string;
  label: string;
  start_time: string;
  end_time: string;
  remaining_capacity: number;
}

export interface PublicSubmitPayload {
  dealer_code: string;
  mobile_number: string;
  preferred_date: string;
  preferred_time_slot: string;
}

export interface PublicSubmitResult {
  dealer_code: string;
  preferred_date: string;
  preferred_time_slot: string;
  submitted_at: string;
  confirmation_message: string;
}

export const publicConfirmApi = {
  async getLinkInfo(token: string): Promise<PublicLinkMetadata> {
    const { data } = await publicClient.get<ApiSuccessResponse<PublicLinkMetadata>>(
      `/public/confirm/${token}/`
    );
    return data.data;
  },

  async getSlotsForDate(token: string, date: string): Promise<AvailableSlotDTO[]> {
    const { data } = await publicClient.get<ApiSuccessResponse<{ date: string; slots: AvailableSlotDTO[] }>>(
      `/public/confirm/${token}/availability/`,
      { params: { date } }
    );
    return data.data.slots;
  },

  async submit(token: string, payload: PublicSubmitPayload): Promise<PublicSubmitResult> {
    const { data } = await publicClient.post<ApiSuccessResponse<PublicSubmitResult>>(
      `/public/confirm/${token}/submit/`,
      payload
    );
    return data.data;
  },
};
