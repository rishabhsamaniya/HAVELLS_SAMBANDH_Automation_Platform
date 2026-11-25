import React, { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  Shield,
  Building2,
  Link2,
  CalendarClock,
  FileBarChart2,
  Settings,
  LogOut,
  Menu,
  X,
} from "lucide-react";

import { BrandLogo } from "@/components/shared/BrandLogo";
import { useAuth } from "@/features/auth/AuthContext";

interface NavItem {
  label: string;
  to: string;
  icon: React.ReactNode;
  permission?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", to: "/dashboard", icon: <LayoutDashboard className="h-[18px] w-[18px]" />, permission: "dashboard.view" },
  { label: "Dealers", to: "/dealers", icon: <Building2 className="h-[18px] w-[18px]" />, permission: "dealers.view" },
  { label: "Confirmation Links", to: "/confirmation-links", icon: <Link2 className="h-[18px] w-[18px]" />, permission: "confirmation_links.view" },
  { label: "Scheduling", to: "/scheduling", icon: <CalendarClock className="h-[18px] w-[18px]" />, permission: "scheduling.view" },
  { label: "Reports", to: "/reports", icon: <FileBarChart2 className="h-[18px] w-[18px]" />, permission: "reports.view" },
  { label: "Users", to: "/users", icon: <Users className="h-[18px] w-[18px]" />, permission: "users.view" },
  { label: "Roles & Permissions", to: "/roles", icon: <Shield className="h-[18px] w-[18px]" />, permission: "roles.view" },
  { label: "Settings", to: "/settings", icon: <Settings className="h-[18px] w-[18px]" /> },
];

export const AdminLayout: React.FC = () => {
  const { user, logout, hasPermission } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const visibleNavItems = NAV_ITEMS.filter(
    (item) => !item.permission || hasPermission(item.permission)
  );

  const primaryRole = user?.roles?.[0]?.name || (user?.is_superuser ? "Super Admin" : "User");

  return (
    <div className="min-h-screen bg-surface-bg flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Left Sidebar */}
      <aside
        className={[
          "fixed lg:static inset-y-0 left-0 z-40 w-[256px] bg-surface-white border-r border-line flex flex-col transition-transform duration-200",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        ].join(" ")}
      >
        <div className="h-20 px-5 flex items-center justify-between border-b border-line">
          <BrandLogo size="sm" />
          <button
            type="button"
            className="lg:hidden text-ink-secondary hover:text-ink-primary"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close navigation"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto" aria-label="Primary Navigation">
          {visibleNavItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                [
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150",
                  isActive
                    ? "bg-brand-tint text-brand-primary border-l-[3px] border-brand-primary"
                    : "text-ink-primary hover:bg-surface-muted",
                ].join(" ")
              }
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-line">
          <div className="mb-3">
            <p className="text-sm font-semibold text-ink-primary truncate">{user?.full_name}</p>
            <p className="text-xs text-ink-secondary truncate">{primaryRole}</p>
          </div>
          <button
            type="button"
            onClick={() => logout()}
            className="w-full flex items-center justify-center gap-2 h-9 rounded-lg border border-line text-xs font-medium text-ink-primary hover:bg-surface-bg transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-surface-white border-b border-line px-4 lg:px-6 flex items-center justify-between">
          <button
            type="button"
            className="lg:hidden p-2 rounded-lg text-ink-primary hover:bg-surface-muted"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="hidden lg:block text-sm font-medium text-ink-secondary">
            Dealer Engagement &amp; Automation Platform
          </div>
          <div className="text-xs text-ink-secondary tabular-nums">
            +91 {user?.mobile_number}
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-6 max-w-[1440px] w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
