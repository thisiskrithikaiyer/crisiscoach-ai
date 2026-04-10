from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from crisiscoach.api.routes.auth import get_current_user

router = APIRouter()


class DailyLogRequest(BaseModel):
    date: str | None = None          # ISO date, defaults to today
    apps_done: int = 0
    networking_done: int = 0
    interviews_scheduled: int = 0
    interviews_completed: int = 0
    interviews_passed: int = 0
    interviews_failed: int = 0
    interview_topics: list[str] = []  # e.g. ["system design", "dynamic programming", "behavioral"]
    leetcode_done: int = 0
    system_design_done: int = 0


@router.post("/daily-log")
async def upsert_daily_log(body: DailyLogRequest, user: dict = Depends(get_current_user)):
    """Upsert today's activity log. One row per user per day."""
    user_id = user.get("sub", "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    log_date = body.date or date.today().isoformat()

    try:
        from crisiscoach.db.supabase import get_client
        sb = get_client()
        # Upsert on (user_id, date) unique index
        sb.table("daily_log").upsert(
            {
                "user_id": user_id,
                "date": log_date,
                "apps_done": body.apps_done,
                "networking_done": body.networking_done,
                "interviews_scheduled": body.interviews_scheduled,
                "interviews_completed": body.interviews_completed,
                "interviews_passed": body.interviews_passed,
                "interviews_failed": body.interviews_failed,
                "interview_topics": body.interview_topics,
                "leetcode_done": body.leetcode_done,
                "system_design_done": body.system_design_done,
            },
            on_conflict="user_id,date",
        ).execute()
        return {"ok": True, "date": log_date}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-log")
async def get_daily_log(days: int = 14, user: dict = Depends(get_current_user)):
    """Return the last N days of activity logs."""
    user_id = user.get("sub", "")
    try:
        from crisiscoach.db.supabase import get_client
        rows = (
            get_client()
            .table("daily_log")
            .select("*")
            .eq("user_id", user_id)
            .order("date", desc=True)
            .limit(days)
            .execute()
        ).data or []
        return list(reversed(rows))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
