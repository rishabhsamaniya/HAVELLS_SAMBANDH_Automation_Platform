"""Action-based remarks catalog for Schedule Management experience tracking."""

EXPERIENCE_ACTION_OPTIONS = [
    {"value": "experience_completed", "label": "Experience Completed"},
    {"value": "experience_on_hold", "label": "Experience on Hold"},
    {"value": "experience_postponed", "label": "Experience Postponed"},
]

EXPERIENCE_ACTION_REMARKS: dict[str, list[str]] = {
    "experience_completed": [
        "Experience delivered successfully to dealer",
        "Surprise handed over & photo/video captured",
        "Dealer satisfied & feedback collected",
        "Experience completed at dealer showroom/outlet",
        "Experience completed at dealer residence/venue",
        "Experience completed with RM/team presence",
    ],
    "experience_on_hold": [
        "Dealer not reachable / phone switched off",
        "Dealer out of station / travelling",
        "Awaiting dealer confirmation on venue/address",
        "Pending RM / internal approval",
        "Gift / surprise inventory pending dispatch",
        "Dealer requested to hold until further notice",
    ],
    "experience_postponed": [
        "Dealer requested new date & time",
        "Dealer busy with personal / family commitment",
        "Dealer shop / showroom closed on scheduled date",
        "Logistics / vendor scheduling delay",
        "Weather / local disruption in dealer area",
        "Rescheduled by RM for better coordination",
    ],
}
