import os
import json
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Maps our Metabase field → the header name to look for in the sheet (case-insensitive)
FIELD_HEADER_MAP = {
    "Pre Login Leap User - Pre User → Name": "name",
    "Pre User ID":                           "pre user id",
    "Pre Login Leap User - Pre User → Phone": "phone",
    "Created At IST":                        "created at",
    "Slot Time in IST":                      "slot",
    "Call Completion":                       "call",
}

_sheet = None
_col_indices: dict[str, int] | None = None  # field_key -> 0-based column index


def _get_sheet():
    global _sheet
    if _sheet is None:
        creds = Credentials.from_service_account_info(
            json.loads(SERVICE_ACCOUNT_JSON), scopes=SCOPES
        )
        gc = gspread.authorize(creds)
        _sheet = gc.open_by_key(SHEET_ID).sheet1
    return _sheet


def _get_col_indices() -> dict[str, int]:
    global _col_indices
    if _col_indices is not None:
        return _col_indices

    headers = [h.strip().lower() for h in _get_sheet().row_values(1)]
    _col_indices = {}

    for field, keyword in FIELD_HEADER_MAP.items():
        for idx, header in enumerate(headers):
            if keyword in header:
                _col_indices[field] = idx
                break

    found = list(_col_indices.keys())
    missing = [f for f in FIELD_HEADER_MAP if f not in _col_indices]
    print(f"Sheets: matched columns {found}", flush=True)
    if missing:
        print(f"Sheets: WARNING — could not find columns for {missing}", flush=True)

    return _col_indices


def log_entry(entry: dict) -> None:
    sheet = _get_sheet()
    col_indices = _get_col_indices()

    if not col_indices:
        print("Sheets: no columns matched, skipping log", flush=True)
        return

    # Build a row sized to the rightmost column we need to write
    max_col = max(col_indices.values())
    row = [""] * (max_col + 1)

    for field, col_idx in col_indices.items():
        val = entry.get(field)
        row[col_idx] = "" if val is None else str(val)

    sheet.append_row(row, value_input_option="USER_ENTERED")
    print(f"Sheets: logged Pre User ID {entry.get('Pre User ID')}", flush=True)
