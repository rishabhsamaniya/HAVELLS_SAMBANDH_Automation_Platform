import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "@/features/auth/AuthContext";
import { LoginPage } from "@/features/auth/LoginPage";
import { ConfirmationLinksPage } from "@/features/confirmations/ConfirmationLinksPage";
import { PublicConfirmationPage } from "@/features/confirmations/PublicConfirmationPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { DealersPage } from "@/features/dealers/DealersPage";
import { ReportsPage } from "@/features/reports/ReportsPage";
import { RolesPage } from "@/features/roles/RolesPage";
import { SchedulingPage } from "@/features/scheduling/SchedulingPage";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { UsersPage } from "@/features/users/UsersPage";
import { AdminLayout } from "@/layouts/AdminLayout";
import { ProtectedRoute } from "@/routes/ProtectedRoute";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/confirm/:token" element={<PublicConfirmationPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AdminLayout />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/dealers" element={<DealersPage />} />
                <Route path="/confirmation-links" element={<ConfirmationLinksPage />} />
                <Route path="/scheduling" element={<SchedulingPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/users" element={<UsersPage />} />
                <Route path="/roles" element={<RolesPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
