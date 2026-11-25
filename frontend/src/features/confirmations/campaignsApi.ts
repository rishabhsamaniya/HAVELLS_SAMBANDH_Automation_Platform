import { apiClient } from "@/api/client";
import { ApiSuccessResponse } from "@/types/api";

export interface CampaignDTO {
  id: string;
  campaign_name: string;
  campaign_code: string;
  start_date: string;
  end_date: string;
  status: string;
}

export const campaignsApi = {
  async list(): Promise<CampaignDTO[]> {
    const { data } = await apiClient.get<ApiSuccessResponse<CampaignDTO[]>>("/campaigns/");
    return data.data;
  },

  async create(payload: {
    campaign_name: string;
    campaign_code: string;
    start_date: string;
    end_date: string;
  }): Promise<CampaignDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<CampaignDTO>>("/campaigns/", payload);
    return data.data;
  },
};
