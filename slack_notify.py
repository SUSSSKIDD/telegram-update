import os
import requests

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "C0B5LG1FL78"


def _fmt(val):
    return str(val) if val is not None else "—"


def send_slack_message(entry: dict):
    name = _fmt(entry.get("Pre Login Leap User - Pre User → Name"))
    pre_user_id = _fmt(entry.get("Pre User ID"))
    phone = _fmt(entry.get("Pre Login Leap User - Pre User → Phone"))
    slot_time = _fmt(entry.get("Slot Time in IST"))
    created_at = _fmt(entry.get("Created At IST"))
    form_id = _fmt(entry.get("Form ID"))
    call_completion = _fmt(entry.get("Call Completion"))

    text = (
        f"🆕 *New Meeting Booked*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:*          {name}\n"
        f"🆔 *Pre User ID:*   {pre_user_id}\n"
        f"📞 *Phone:*         {phone}\n"
        f"📅 *Slot Time:*     {slot_time}\n"
        f"🕐 *Created At:*    {created_at}\n"
        f"📋 *Form ID:*       {form_id}\n"
        f"✅ *Call Done:*     {call_completion}"
    )

    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        json={"channel": SLACK_CHANNEL, "text": text},
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        raise Exception(f"Slack API error: {result.get('error')}")
