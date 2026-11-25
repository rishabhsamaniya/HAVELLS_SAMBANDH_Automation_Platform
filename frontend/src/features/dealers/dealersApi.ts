import { apiClient } from "@/api/client";
import { ApiSuccessResponse } from "@/types/api";

export interface DealerDTO {
  id: string;
  dealer_code: string;
  mobile_number: string;
  status: "active" | "inactive";
  assigned_rm: string;
  assigned_rm_name: string;
  assigned_rm_mobile: string;
  created_at: string;
  updated_at: string;
}

export interface DealerImportSummary {
  total_rows: number;
  created_count: number;
  failed_count: number;
  errors: Array<{ row_number: number; dealer_code: string; errors: string[] }>;
}

export const dealersApi = {
  async list(params?: Record<string, string | number>): Promise<ApiSuccessResponse<DealerDTO[]>> {
    const { data } = await apiClient.get<ApiSuccessResponse<DealerDTO[]>>("/dealers/", { params });
    return data;
  },

  async create(payload: {
    dealer_code: string;
    mobile_number: string;
    assigned_rm: string;
    status?: string;
  }): Promise<DealerDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<DealerDTO>>("/dealers/", payload);
    return data.data;
  },

  async deactivate(id: string): Promise<DealerDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<DealerDTO>>(`/dealers/${id}/deactivate/`);
    return data.data;
  },

  async importExcel(file: File): Promise<DealerImportSummary> {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await apiClient.post<ApiSuccessResponse<DealerImportSummary>>(
      "/dealers/import/",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return data.data;
  },

  async downloadTemplate(): Promise<Blob> {
    const { data } = await apiClient.get("/dealers/import-template/", {
      responseType: "blob",
    });
    return data;
  },

  async exportFile(format: "xlsx" | "csv" = "xlsx"): Promise<Blob> {
    const { data } = await apiClient.get("/dealers/export/", {
      params: { format },
      responseType: "blob",
    });
    return data;
  },
};
