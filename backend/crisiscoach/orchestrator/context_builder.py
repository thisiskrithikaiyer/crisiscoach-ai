"""Assembles minimal user context for the current request without blocking the response."""
from __future__ import annotations
from datetime import date
from crisiscoach.orchestrator.state import CrisisCoachState


async def build_context(state: CrisisCoachState) -> dict:
    """
    Fetch lightweight user snapshot from Supabase and return a partial state update.
    Falls back gracefully if DB is unavailable so the agent can still respond.
    """
    user_id = state.get("user_id", "")
    if not user_id:
        return {}

    try:
        from crisiscoach.db.supabase import get_client
        sb = get_client()

        # Latest check-in
        checkin_row = (
            sb.table("checkins")
            .select("mood_score, energy_score, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        checkin = checkin_row.data[0] if checkin_row.data else {}

        # User profile
        profile_row = (
            sb.table("users")
            .select("layoff_date, visa_deadline, runway_weeks, open_tasks")
            .eq("id", user_id)
            .single()
            .execute()
        )
        profile = profile_row.data or {}

        days_since_layoff = None
        if profile.get("layoff_date"):
            layoff = date.fromisoformat(profile["layoff_date"])
            days_since_layoff = (date.today() - layoff).days

        visa_deadline_days = None
        if profile.get("visa_deadline"):
            deadline = date.fromisoformat(profile["visa_deadline"])
            visa_deadline_days = (deadline - date.today()).days

        return {
            "days_since_layoff": days_since_layoff,
            "visa_deadline_days": visa_deadline_days,
            "runway_weeks": profile.get("runway_weeks"),
            "mood_score": checkin.get("mood_score"),
            "energy_score": checkin.get("energy_score"),
            "open_tasks": profile.get("open_tasks"),
        }
    except Exception:
        return {}
