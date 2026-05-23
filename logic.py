import pandas as pd
from telegram_client import send_new_meeting

# In-memory set of notified pre_user_ids.
# On startup this is pre-populated with today's existing entries so restarts
# don't cause duplicate notifications.
_seen_ids: set[str] = set()


def init_seen(df: pd.DataFrame) -> None:
    """Silently absorb all current entries on startup — no notifications sent."""
    for uid in df["Pre User ID"].dropna().astype(str):
        _seen_ids.add(uid.strip())


def run_checks(df: pd.DataFrame) -> dict:
    new_count = 0

    for _, row in df.iterrows():
        uid = str(row.get("Pre User ID", "")).strip()
        if not uid or uid == "nan":
            continue
        if uid not in _seen_ids:
            send_new_meeting(row.to_dict())
            _seen_ids.add(uid)
            new_count += 1

    return {"new_entries": new_count, "total": len(df)}
