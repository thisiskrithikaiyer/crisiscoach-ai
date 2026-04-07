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


@router.get("/plan/today", response_model=PlanResponse)
async def get_today_plan(user: dict = Depends(get_current_user)):
    user_id = user.get("sub", "")
    try:
        from crisiscoach.db.supabase import get_client
        from datetime import date

        sb = get_client()
        today = date.today().isoformat()
        result = (
            sb.table("plans")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", today)
            .limit(1)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="No plan for today. Check back after your evening check-in.")
        plan = result.data[0]
        tasks = (
            sb.table("plan_tasks")
            .select("*")
            .eq("plan_id", plan["id"])
            .order("priority")
            .execute()
        )
        return PlanResponse(
            plan_id=plan["id"],
            date=today,
            tasks=[PlanTask(**t) for t in tasks.data],
            coach_note=plan.get("coach_note", ""),
        )
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
    """Enqueue a plan generation job — non-blocking."""
    user_id = user.get("sub", "")
    try:
        from crisiscoach.db.redis import get_redis
        import json

        r = get_redis()
        r.rpush("plan_queue", json.dumps({"user_id": user_id}))
        return {"ok": True, "message": "Plan generation queued. Check back shortly."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
