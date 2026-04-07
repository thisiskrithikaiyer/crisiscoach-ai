"""Daily check — nightly aggregation of mood/energy trends written to analytics table."""
from datetime import date, timedelta


async def aggregate_for_user(user_id: str) -> dict:
    """Compute weekly averages and persist to user_analytics table."""
    from crisiscoach.db.supabase import get_client
    sb = get_client()

    week_ago = (date.today() - timedelta(days=7)).isoformat()
    rows = (
        sb.table("checkins")
        .select("mood_score, energy_score, created_at")
        .eq("user_id", user_id)
        .gte("created_at", week_ago)
        .execute()
    )
    checkins = rows.data
    if not checkins:
        return {"aggregated": False}

    avg_mood = sum(c["mood_score"] for c in checkins) / len(checkins)
    avg_energy = sum(c["energy_score"] for c in checkins) / len(checkins)
    checkin_count = len(checkins)

    sb.table("user_analytics").upsert({
        "user_id": user_id,
        "week_start": week_ago,
        "avg_mood": round(avg_mood, 2),
        "avg_energy": round(avg_energy, 2),
        "checkin_count": checkin_count,
        "updated_at": date.today().isoformat(),
    }, on_conflict="user_id,week_start").execute()

    return {
        "aggregated": True,
        "avg_mood": avg_mood,
        "avg_energy": avg_energy,
        "checkin_count": checkin_count,
    }
