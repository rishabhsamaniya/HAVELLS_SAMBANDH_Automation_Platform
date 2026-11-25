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

  it("auto-fills Dealer Code and Mobile Number, requires only Date & Time selection, and displays exact approved success message", async () => {
    vi.mocked(publicConfirmApi.getLinkInfo).mockResolvedValue({
      dealer_code: "HVL-1001",
      mobile_number: "9876543210",
      campaign_name: "Sambandh Nov 2026",
      allowed_month: "2026-11",
      timezone: "Asia/Kolkata",
      expires_at: "2026-11-30T23:59:59+05:30",
      available_dates: ["2026-11-24", "2026-11-25"],
      has_available_dates: true,
      default_slots: [
        {
          id: "slot-0",
          label: "12:00 AM – 01:00 AM",
          start_time: "00:00",
          end_time: "01:00",
          remaining_capacity: 1,
        },
        {
          id: "slot-1",
          label: "11:00 PM – 12:00 AM",
          start_time: "23:00",
          end_time: "00:00",
          remaining_capacity: 1,
        },
      ],
    });
    vi.mocked(publicConfirmApi.getSlotsForDate).mockResolvedValue([
      {
        id: "slot-0",
        label: "12:00 AM – 01:00 AM",
        start_time: "00:00",
        end_time: "01:00",
        remaining_capacity: 1,
      },
      {
        id: "slot-1",
        label: "11:00 PM – 12:00 AM",
        start_time: "23:00",
        end_time: "00:00",
        remaining_capacity: 1,
      },
    ]);
    vi.mocked(publicConfirmApi.submit).mockResolvedValue({
      dealer_code: "HVL-1001",
      preferred_date: "2026-11-24",
      preferred_time_slot: "11:00 PM – 12:00 AM",
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

    // Dealer Code & Mobile Number are auto-filled and read-only — user only selects Date & Time!
    expect(screen.getByLabelText(/Dealer Code/i)).toHaveValue("HVL-1001");
    expect(screen.getByLabelText(/Mobile Number/i)).toHaveValue("9876543210");

    // Time slot dropdown is enabled immediately with 24-hour default slots
    expect(screen.getByLabelText(/Preferred Time Slot/i)).not.toBeDisabled();
    expect(screen.getByRole("option", { name: "12:00 AM – 01:00 AM" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "11:00 PM – 12:00 AM" })).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText(/Preferred Date/i), "2026-11-24");

    await waitFor(() => {
      expect(publicConfirmApi.getSlotsForDate).toHaveBeenCalledWith("valid-token", "2026-11-24");
    });
    await user.selectOptions(screen.getByLabelText(/Preferred Time Slot/i), "slot-1");

    await user.click(screen.getByRole("button", { name: /^Confirm$/i }));

    await waitFor(() => {
      expect(screen.getByText(EXACT_SUCCESS_MSG)).toBeInTheDocument();
    });
  });

  it("displays branded unavailable state when no future dates remain in allowed month", async () => {
    vi.mocked(publicConfirmApi.getLinkInfo).mockResolvedValue({
      dealer_code: "HVL-1001",
      mobile_number: "9876543210",
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
