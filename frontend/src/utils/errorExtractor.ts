import { AxiosError } from "axios";
import { ApiErrorResponse } from "@/types/api";

/**
 * Extracts a clear, user-friendly error message including field-level details from API errors.
 */
export function extractApiErrorMessage(err: unknown, fallback = "Something went wrong. Please try again."): string {
  const axiosErr = err as AxiosError<ApiErrorResponse>;
  const apiError = axiosErr?.response?.data?.error;
  if (!apiError) return fallback;

  const detailMessages: string[] = [];
  if (apiError.details && typeof apiError.details === "object") {
    for (const [field, value] of Object.entries(apiError.details)) {
      const label = field === "non_field_errors" ? "" : `${field.replace(/_/g, " ")}: `;
      if (Array.isArray(value)) {
        value.forEach((v) => detailMessages.push(`${label}${String(v)}`));
      } else if (typeof value === "string") {
        detailMessages.push(`${label}${value}`);
      }
    }
  }

  if (detailMessages.length > 0) {
    return detailMessages.join(" • ");
  }
  return apiError.message || fallback;
}
