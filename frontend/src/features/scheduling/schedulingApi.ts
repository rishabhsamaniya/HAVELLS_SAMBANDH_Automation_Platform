import { apiClient } from "@/api/client";
import { ApiSuccessResponse } from "@/types/api";

export interface OperatingHoursConfigDTO {
  id: string;
  opening_time: string;
  closing_time: string;
  slot_duration: number;
  default_capacity: number;
  allow_same_day_booking: boolean;
  is_active: boolean;
}

export interface TimeSlotDTO {
  id: string;
  start_time: string;
  end_time: string;
  display_label: string;
  slot_duration: number;
  max_capacity: number;
  is_active: boolean;
}

export interface BookingDTO {
  id: string;
  dealer_code: string;
  dealer_mobile: string;
  assigned_rm_name: string;
  campaign_name: string;
  preferred_date: string;
  preferred_time_slot: string;
  time_slot_label: string;
  submission_status: string;
  submitted_at: string;
}

export const schedulingApi = {
  async getConfig(): Promise<OperatingHoursConfigDTO> {
    const { data } = await apiClient.get<ApiSuccessResponse<OperatingHoursConfigDTO>>("/scheduling/config/");
    return data.data;
  },

  async updateConfig(payload: {
    opening_time: string;
    closing_time: string;
    slot_duration: number;
    default_capacity: number;
    allow_same_day_booking: boolean;
  }): Promise<OperatingHoursConfigDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<OperatingHoursConfigDTO>>("/scheduling/config/", payload);
    return data.data;
  },

  async listSlots(): Promise<TimeSlotDTO[]> {
    const { data } = await apiClient.get<ApiSuccessResponse<TimeSlotDTO[]>>("/scheduling/slots/");
    return data.data;
  },

  async updateSlot(id: string, payload: Partial<Pick<TimeSlotDTO, "max_capacity" | "is_active">>): Promise<TimeSlotDTO> {
    const { data } = await apiClient.patch<ApiSuccessResponse<TimeSlotDTO>>(`/scheduling/slots/${id}/`, payload);
    return data.data;
  },

  async listBookings(): Promise<BookingDTO[]> {
    const { data } = await apiClient.get<ApiSuccessResponse<BookingDTO[]>>("/scheduling/bookings/");
    return data.data;
  },

  async cancelBooking(id: string, reason: string): Promise<BookingDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<BookingDTO>>(
      `/scheduling/bookings/${id}/cancel/`,
      { reason }
    );
    return data.data;
  },
};
