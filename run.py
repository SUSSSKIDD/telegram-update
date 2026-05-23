import os
import hashlib
import requests
from datetime import datetime
import pytz
import redis
from flask import Flask, jsonify

# ── Config ────────────────────────────────────────────────────────────────────
METABASE_URL      = os.environ["METABASE_URL"].rstrip("/")
METABASE_EMAIL    = os.environ["METABASE_EMAIL"]
METABASE_PASSWORD = os.environ["METABASE_PASSWORD"]
QUESTION_ID       = int(os.environ.get("METABASE_QUESTION_ID", "33308"))
TG_TOKEN          = os.environ["TELEGRAM_BOT_TOKEN"]
TG_CHAT_ID        = os.environ["TELEGRAM_CHAT_ID"]
REDIS_URL         = os.environ["UPSTASH_REDIS_URL"]
PORT              = int(os.environ.get("PORT", "8000"))

IST               = pytz.timezone("Asia/Kolkata")
ENTRY_TTL_SECONDS = 7 * 24 * 3600

app = Flask(__name__)

# ── Redis ─────────────────────────────────────────────────────────────────────
_redis = redis.from_url(REDIS_URL, decode_responses=True)


def _entry_key(pre_user_id: str) -> str:
    h = hashlib.sha256(pre_user_id.encode()).hexdigest()[:16]
    return f"meeting_seen:{h}"


def is_seen(pre_user_id: str) -> bool:
    return bool(_redis.exists(_entry_key(pre_user_id)))


def mark_seen(pre_user_id: str) -> None:
    _redis.setex(_entry_key(pre_user_id), ENTRY_TTL_SECONDS, "1")


# ── Metabase ──────────────────────────────────────────────────────────────────
def get_session_token() -> str:
    resp = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": METABASE_EMAIL, "password": METABASE_PASSWORD},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def fetch_todays_entries() -> list[dict]:
    today = datetime.now(IST).strftime("%Y-%m-%d")
    token = get_session_token()

    resp = requests.post(
        f"{METABASE_URL}/api/card/{QUESTION_ID}/query/json",
        headers={"X-Metabase-Session": token, "Content-Type": "application/json"},
        json={
            "parameters": [
                {"type": "date/single", "target": ["variable", ["template-tag", "start_date"]], "value": today},
                {"type": "date/single", "target": ["variable", ["template-tag", "end_date"]], "value": today},
            ]
        },
        timeout=60,
    )
    resp.raise_for_status()

    rows = resp.json()
    return [{k.strip(): v for k, v in row.items()} for row in rows] if rows else []


# ── Telegram ──────────────────────────────────────────────────────────────────
def _fmt(val) -> str:
    return "—" if val is None else str(val)


def send_telegram(entry: dict) -> None:
    msg = (
        "🆕 <b>New Meeting Booked</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Name:</b>         {_fmt(entry.get('Pre Login Leap User - Pre User → Name'))}\n"
        f"🆔 <b>Pre User ID:</b>  {_fmt(entry.get('Pre User ID'))}\n"
        f"📞 <b>Phone:</b>        {_fmt(entry.get('Pre Login Leap User - Pre User → Phone'))}\n"
        f"📅 <b>Slot Time:</b>    {_fmt(entry.get('Slot Time in IST'))}\n"
        f"🕐 <b>Created At:</b>   {_fmt(entry.get('Created At IST'))}\n"
        f"📋 <b>Form ID:</b>      {_fmt(entry.get('Form ID'))}\n"
        f"✅ <b>Call Done:</b>    {_fmt(entry.get('Call Completion'))}"
    )
    resp = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"},
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        raise Exception(f"Telegram error: {result.get('description')}")


# ── Flask endpoints ───────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/run")
def run():
    try:
        entries = fetch_todays_entries()
        new_count = 0

        for entry in entries:
            uid = str(entry.get("Pre User ID", "")).strip()
            if not uid or uid == "None":
                continue
            if not is_seen(uid):
                send_telegram(entry)
                mark_seen(uid)
                new_count += 1
                print(f"Notified: {uid} — {entry.get('Pre Login Leap User - Pre User → Name')}", flush=True)

        print(f"Done: {new_count} new / {len(entries)} total", flush=True)
        return jsonify({"status": "ok", "new_entries": new_count, "total": len(entries)})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
