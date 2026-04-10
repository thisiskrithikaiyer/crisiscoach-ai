from fastapi import APIRouter, Depends, HTTPException
from crisiscoach.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/goal-plan")
async def get_latest_goal_plan(user: dict = Depends(get_current_user)):
    """Return the most recent goal plan for the authenticated user."""
    user_id = user.get("sub", "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from crisiscoach.db.supabase import get_client
        row = (
            get_client()
            .table("goal_plan")
            .select("id, date, goal_stratergy, revision_analytics, goal_committed_at, next_revision_date, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not row.data:
            raise HTTPException(status_code=404, detail="No goal plan found")
        return row.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
