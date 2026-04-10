from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from crisiscoach.api.routes.auth import get_current_user

router = APIRouter()


class PlanTask(BaseModel):
    id: str
    title: str
    category: str        # job_search | wellness | admin | interview_prep
    priority: int        # 1 (high) - 3 (low)
    completed: bool
    due_date: str | None = None


class PlanResponse(BaseModel):
    plan_id: str
    date: str
    tasks: list[PlanTask]
    coach_note: str


class TaskUpdateRequest(BaseModel):
    completed: bool


@router.get("/plan/today")
async def get_today_plan(user: dict = Depends(get_current_user)):
    user_id = user.get("sub", "")
    try:
        from crisiscoach.db.supabase import get_client
        from datetime import date

        sb = get_client()
        today = date.today().isoformat()
        result = (
            sb.table("plans")
            .select("id, date, coach_note, plan_json, schedule, priority_mode")
            .eq("user_id", user_id)
            .eq("date", today)
            .limit(1)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="No plan for today.")
        plan = result.data[0]
        return {
            "plan_id": plan["id"],
            "date": today,
            "coach_note": plan.get("coach_note", ""),
            "priority_mode": plan.get("priority_mode", "standard"),
            "schedule": plan.get("schedule") or {},
            **plan.get("plan_json", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/plan/task/{task_id}")
async def update_task(task_id: str, body: TaskUpdateRequest, user: dict = Depends(get_current_user)):
    try:
        from crisiscoach.db.supabase import get_client
        sb = get_client()
        sb.table("plan_tasks").update({"completed": body.completed}).eq("id", task_id).execute()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan/generate")
async def trigger_plan_generation(user: dict = Depends(get_current_user)):
    """Generate today's daily plan immediately (no Redis queue)."""
    user_id = user.get("sub", "")
    try:
        from crisiscoach.agents.background.daily_check import build_daily_plan
        result = await build_daily_plan(user_id)
        return {"ok": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
