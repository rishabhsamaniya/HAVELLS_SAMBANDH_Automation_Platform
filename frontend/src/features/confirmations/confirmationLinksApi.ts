import { apiClient } from "@/api/client";
import { ApiSuccessResponse } from "@/types/api";

export interface ConfirmationLinkDTO {
  id: string;
  dealer: string;
  dealer_code: string;
  dealer_mobile: string;
  campaign: string;
  campaign_name: string;
  assigned_rm: string;
  assigned_rm_name: string;
  allowed_month: string;
  status: string;
  shared_at: string | null;
  expires_at: string;
  max_submissions: number;
  submission_count: number;
  is_regenerated: boolean;
  regeneration_count: number;
  can_copy: boolean;
  can_regenerate: boolean;
  created_at: string;
  shareable_url?: string;
  share_message?: string;
}

export interface BulkGenerateResultDTO {
  created_count: number;
  skipped_count: number;
  links: ConfirmationLinkDTO[];
  skipped: Array<{ dealer_id: string; dealer_code: string; reason: string }>;
}

export const confirmationLinksApi = {
  async list(params?: Record<string, string>): Promise<ApiSuccessResponse<ConfirmationLinkDTO[]>> {
    const { data } = await apiClient.get<ApiSuccessResponse<ConfirmationLinkDTO[]>>(
      "/confirmation-links/",
      { params }
    );
    return data;
  },

  async generate(payload: { dealer: string; campaign: string }): Promise<ConfirmationLinkDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<ConfirmationLinkDTO>>(
      "/confirmation-links/",
      payload
    );
    return data.data;
  },

  async bulkGenerate(payload: {
    campaign: string;
    dealer_ids?: string[];
    select_all_active?: boolean;
  }): Promise<BulkGenerateResultDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<BulkGenerateResultDTO>>(
      "/confirmation-links/bulk-generate/",
      payload
    );
    return data.data;
  },

  async copyShare(id: string): Promise<ConfirmationLinkDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<ConfirmationLinkDTO>>(
      `/confirmation-links/${id}/copy-share/`
    );
    return data.data;
  },

  async regenerate(id: string): Promise<ConfirmationLinkDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<ConfirmationLinkDTO>>(
      `/confirmation-links/${id}/regenerate/`
    );
    return data.data;
  },

  async markShared(id: string): Promise<ConfirmationLinkDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<ConfirmationLinkDTO>>(
      `/confirmation-links/${id}/mark-shared/`
    );
    return data.data;
  },

  async deactivate(id: string): Promise<ConfirmationLinkDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<ConfirmationLinkDTO>>(
      `/confirmation-links/${id}/deactivate/`
    );
    return data.data;
  },
};
