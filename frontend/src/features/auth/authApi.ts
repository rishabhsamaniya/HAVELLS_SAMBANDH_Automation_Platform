import { apiClient } from "@/api/client";
import { ApiSuccessResponse } from "@/types/api";

export interface UserRoleSummary {
  id: string;
  name: string;
  code: string;
}

export interface AuthUser {
  id: string;
  full_name: string;
  mobile_number: string;
  email: string | null;
  is_active: boolean;
  is_superuser: boolean;
  last_login: string | null;
  roles: UserRoleSummary[];
  permissions: string[];
}

export interface LoginPayload {
  mobile_number: string;
  password: string;
}

export interface LoginResponseData {
  access: string;
  user: AuthUser;
}

export const authApi = {
  async login(payload: LoginPayload): Promise<LoginResponseData> {
    const { data } = await apiClient.post<ApiSuccessResponse<LoginResponseData>>("/auth/login/", payload);
    return data.data;
  },

  async refresh(): Promise<{ access: string }> {
    const { data } = await apiClient.post<ApiSuccessResponse<{ access: string }>>("/auth/refresh/");
    return data.data;
  },

  async me(): Promise<AuthUser> {
    const { data } = await apiClient.get<ApiSuccessResponse<AuthUser>>("/auth/me/");
    return data.data;
  },

  async logout(): Promise<void> {
    await apiClient.post("/auth/logout/");
  },

  async forgotPassword(mobile_number: string): Promise<string> {
    const { data } = await apiClient.post<ApiSuccessResponse<unknown>>("/auth/forgot-password/", {
      mobile_number,
    });
    return data.message;
  },
};
