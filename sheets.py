import os
import json
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Ordered headers that will be written to row 1 if the sheet is empty
HEADERS = [
    "Name",
    "Pre User ID",
    "Phone Number",
    "Date & Time of Booking (IST)",
    "Slot Booked (IST)",
    "Call Completed",
]

# Maps each header → the Metabase field key
HEADER_TO_FIELD = {
    "Name":                        "Pre Login Leap User - Pre User → Name",
    "Pre User ID":                 "Pre User ID",
    "Phone Number":                "Pre Login Leap User - Pre User → Phone",
    "Date & Time of Booking (IST)": "Created At IST",
    "Slot Booked (IST)":           "Slot Time in IST",
    "Call Completed":              "Call Completion",
}

_sheet = None


def _get_sheet():
    global _sheet
    if _sheet is None:
        creds = Credentials.from_service_account_info(
            json.loads(SERVICE_ACCOUNT_JSON), scopes=SCOPES
        )
        gc = gspread.authorize(creds)
        _sheet = gc.open_by_key(SHEET_ID).sheet1
    return _sheet


def _get_headers() -> list[str]:
    result = _get_sheet().get("A1:Z1")
    return result[0] if result else []


def _ensure_headers():
    if not _get_headers():
        _get_sheet().append_row(HEADERS, value_input_option="USER_ENTERED")
        print("Sheets: wrote header row", flush=True)


def _next_empty_row() -> int:
    col_a = _get_sheet().col_values(1)
    return len(col_a) + 1


def log_entry(entry: dict) -> None:
    _ensure_headers()

    headers = _get_headers()
    print(f"Sheets: headers found → {headers}", flush=True)

    row = [""] * len(headers)
    matched = []

    for idx, header in enumerate(headers):
        field = HEADER_TO_FIELD.get(header)
        if field:
            val = entry.get(field)
            row[idx] = "" if val is None else str(val)
            matched.append(header)

    target_row = _next_empty_row()
    print(f"Sheets: matched {matched}, writing to row {target_row} → {row}", flush=True)

    sheet = _get_sheet()
    sheet.update(f"A{target_row}", [row], value_input_option="USER_ENTERED")
    print(f"Sheets: logged Pre User ID {entry.get('Pre User ID')} → row {target_row}", flush=True)
