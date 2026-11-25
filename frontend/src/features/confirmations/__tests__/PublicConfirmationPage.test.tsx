import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PublicConfirmationPage } from "../PublicConfirmationPage";
import { publicConfirmApi } from "../publicConfirmApi";

vi.mock("../publicConfirmApi", () => ({
  publicConfirmApi: {
    getLinkInfo: vi.fn(),
    getSlotsForDate: vi.fn(),
    submit: vi.fn(),
  },
}));

const EXACT_SUCCESS_MSG =
  "Thank You, Your Confirmation form are submited successfully. If you want to change date and time so please connect to your RM.";

describe("PublicConfirmationPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders strictly 4 fields, submits confirmation, and displays exact approved success message", async () => {
    vi.mocked(publicConfirmApi.getLinkInfo).mockResolvedValue({
      campaign_name: "Sambandh Nov 2026",
      allowed_month: "2026-11",
      timezone: "Asia/Kolkata",
      expires_at: "2026-11-30T23:59:59+05:30",
      available_dates: ["2026-11-24", "2026-11-25"],
      has_available_dates: true,
    });
    vi.mocked(publicConfirmApi.getSlotsForDate).mockResolvedValue([
      {
        id: "slot-1",
        label: "10:00 AM – 11:00 AM",
        start_time: "10:00",
        end_time: "11:00",
        remaining_capacity: 1,
      },
    ]);
    vi.mocked(publicConfirmApi.submit).mockResolvedValue({
      dealer_code: "HVL-1001",
      preferred_date: "2026-11-24",
      preferred_time_slot: "10:00 AM – 11:00 AM",
      submitted_at: "2026-11-23T12:00:00Z",
      confirmation_message: EXACT_SUCCESS_MSG,
    });

    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/confirm/valid-token"]}>
        <Routes>
          <Route path="/confirm/:token" element={<PublicConfirmationPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Date Confirmation Form")).toBeInTheDocument();
    });

    // Ensure forbidden fields are NOT present
    expect(screen.queryByLabelText(/Dealer Name/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Experience/i)).not.toBeInTheDocument();

    // Fill the strictly 4 fields
    await user.type(screen.getByLabelText(/Dealer Code/i), "HVL-1001");
    await user.type(screen.getByLabelText(/Mobile Number/i), "9876543210");
    await user.selectOptions(screen.getByLabelText(/Preferred Date/i), "2026-11-24");

    await waitFor(() => {
      expect(screen.getByRole("option", { name: "10:00 AM – 11:00 AM" })).toBeInTheDocument();
    });
    await user.selectOptions(screen.getByLabelText(/Preferred Time Slot/i), "slot-1");

    await user.click(screen.getByRole("button", { name: /^Confirm$/i }));

    await waitFor(() => {
      expect(screen.getByText(EXACT_SUCCESS_MSG)).toBeInTheDocument();
    });
  });

  it("displays branded unavailable state when no future dates remain in allowed month", async () => {
    vi.mocked(publicConfirmApi.getLinkInfo).mockResolvedValue({
      campaign_name: "Sambandh Nov 2026",
      allowed_month: "2026-11",
      timezone: "Asia/Kolkata",
      expires_at: "2026-11-30T23:59:59+05:30",
      available_dates: [],
      has_available_dates: false,
    });

    render(
      <MemoryRouter initialEntries={["/confirm/last-day-token"]}>
        <Routes>
          <Route path="/confirm/:token" element={<PublicConfirmationPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No Available Dates Remaining/i)).toBeInTheDocument();
    });
  });
});
