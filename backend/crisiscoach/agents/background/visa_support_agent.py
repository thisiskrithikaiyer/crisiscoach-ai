"""Visa support agent — daily grace period countdown and action alerts."""
from datetime import date
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

ALERT_THRESHOLDS_DAYS = [60, 30, 14, 7, 3, 1]


async def run_for_user(user_id: str) -> dict:
    from crisiscoach.db.supabase import get_client
    sb = get_client()

    profile = sb.table("users").select("visa_deadline, visa_type").eq("id", user_id).single().execute()
    data = profile.data or {}

    if not data.get("visa_deadline"):
        return {"skipped": True, "reason": "no_visa_deadline"}

    deadline = date.fromisoformat(data["visa_deadline"])
    days_left = (deadline - date.today()).days

    if days_left not in ALERT_THRESHOLDS_DAYS:
        return {"days_left": days_left, "alert_sent": False}

    visa_type = data.get("visa_type", "work visa")
    message = _generate_visa_alert(days_left, visa_type)

    sb.table("notifications").insert({
        "user_id": user_id,
        "type": "visa_alert",
        "body": message,
        "days_until_deadline": days_left,
    }).execute()

    return {"days_left": days_left, "alert_sent": True, "message": message}


def _generate_visa_alert(days_left: int, visa_type: str) -> str:
    prompt = (
        f"Write a concise, urgent-but-calm alert for someone on a {visa_type} "
        f"with {days_left} day(s) remaining in their grace period after a layoff. "
        "Include the single most critical action they must take now. Under 80 words."
    )
    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content
