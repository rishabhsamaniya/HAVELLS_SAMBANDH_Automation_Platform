import { apiClient } from "@/api/client";
import { ApiSuccessResponse } from "@/types/api";

export interface AuditLogDTO {
  id: string;
  user_name: string;
  user_mobile: string | null;
  action: string;
  module: string;
  object_type: string;
  object_id: string;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export const auditLogsApi = {
  async list(params?: Record<string, string>): Promise<AuditLogDTO[]> {
    const { data } = await apiClient.get<ApiSuccessResponse<AuditLogDTO[]>>("/audit-logs/", {
      params,
    });
    return data.data;
  },
};
