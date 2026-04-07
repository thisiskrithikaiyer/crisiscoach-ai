"""Planner agent — builds tomorrow's prioritized action plan after evening check-in."""
import json
from datetime import date, timedelta
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


async def generate_plan(user_id: str) -> dict:
    """
    Pull user profile + recent check-ins from Supabase, generate a structured plan,
    and persist it. Called by plan_worker.py.
    """
    from crisiscoach.db.supabase import get_client
    sb = get_client()

    profile_row = sb.table("users").select("*").eq("id", user_id).single().execute()
    profile = profile_row.data or {}

    checkins = (
        sb.table("checkins")
        .select("mood_score, energy_score, wins, blockers, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(3)
        .execute()
    )

    context = json.dumps({
        "profile": profile,
        "recent_checkins": checkins.data,
        "target_date": (date.today() + timedelta(days=1)).isoformat(),
    }, default=str)

    system = (
        "You are a rigorous job-search coach. Given user context, generate a focused daily plan. "
        "Output valid JSON only: "
        '{"coach_note": "...", "tasks": [{"title": "...", "category": "job_search|wellness|admin|interview_prep", "priority": 1-3}]}. '
        "Max 6 tasks. Prioritize ruthlessly. Be specific — no generic advice."
    )
    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=1024,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": context},
        ],
    )
    raw = resp.choices[0].message.content.strip()
    plan_data = json.loads(raw)

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    plan_row = sb.table("plans").insert({
        "user_id": user_id,
        "date": tomorrow,
        "coach_note": plan_data.get("coach_note", ""),
    }).execute()
    plan_id = plan_row.data[0]["id"]

    tasks = [
        {"plan_id": plan_id, "user_id": user_id, "completed": False, **t}
        for t in plan_data.get("tasks", [])
    ]
    if tasks:
        sb.table("plan_tasks").insert(tasks).execute()

    return {"plan_id": plan_id, "tasks_created": len(tasks)}
