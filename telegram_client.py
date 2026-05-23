import os
import requests

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def _fmt(val) -> str:
    if val is None or (isinstance(val, float) and val != val):
        return "—"
    return str(val)


def _send(text: str) -> None:
    resp = requests.post(
        API_URL,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        raise Exception(f"Telegram error: {result.get('description')}")


def send_new_meeting(entry: dict) -> None:
    name        = _fmt(entry.get("Pre Login Leap User - Pre User → Name"))
    pre_user_id = _fmt(entry.get("Pre User ID"))
    phone       = _fmt(entry.get("Pre Login Leap User - Pre User → Phone"))
    slot_time   = _fmt(entry.get("Slot Time in IST"))
    created_at  = _fmt(entry.get("Created At IST"))
    form_id     = _fmt(entry.get("Form ID"))
    call_done   = _fmt(entry.get("Call Completion"))

    msg = (
        "🆕 <b>New Meeting Booked</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Name:</b>          {name}\n"
        f"🆔 <b>Pre User ID:</b>   {pre_user_id}\n"
        f"📞 <b>Phone:</b>         {phone}\n"
        f"📅 <b>Slot Time:</b>     {slot_time}\n"
        f"🕐 <b>Created At:</b>    {created_at}\n"
        f"📋 <b>Form ID:</b>       {form_id}\n"
        f"✅ <b>Call Done:</b>     {call_done}"
    )
    _send(msg)
