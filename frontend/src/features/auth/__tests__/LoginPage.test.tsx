import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { LoginPage } from "../LoginPage";

vi.mock("../AuthContext", () => ({
  useAuth: () => ({
    login: vi.fn().mockResolvedValue(undefined),
    user: null,
    isLoading: false,
    isAuthenticated: false,
    logout: vi.fn(),
    hasPermission: () => false,
  }),
}));

describe("LoginPage", () => {
  it("validates 10-digit Indian mobile number before submission", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Mobile Number/i), "12345");
    await user.type(screen.getByPlaceholderText(/Enter your password/i), "StrongPass@123");
    await user.click(screen.getByRole("button", { name: /Sign In/i }));

    await waitFor(() => {
      expect(screen.getByText(/Enter a valid 10-digit Indian mobile number/i)).toBeInTheDocument();
    });
  });
});
