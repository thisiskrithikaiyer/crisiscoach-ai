"""
Daily Plan Builder — orchestrates sub-agents to build tomorrow's smart daily plan.

Flow:
  1. signal_analyzer  → reads all DB data, computes signals
  2. plan_prioritizer → determines priority mode + adjusted targets (pure logic)
  3. planner          → determines next leetcode topic from curriculum
  4. schedule_builder → builds morning/midday/evening time blocks
  5. saves to plans table with full schedule, signals, priority_mode
"""
from datetime import date, timedelta

from crisiscoach.agents.background.signal_analyzer import analyze
from crisiscoach.agents.background.plan_prioritizer import prioritize
from crisiscoach.agents.background.schedule_builder import build_schedule, build_coach_note
from crisiscoach.agents.background.planner import (
    LEETCODE_CURRICULUM, BEHAVIORAL_ROTATION,
    _get_next_leetcode_topic, _get_behavioral_focus,
)


async def build_daily_plan(user_id: str) -> dict:
    from crisiscoach.db.supabase import get_client
    sb = get_client()

    today = date.today()
    tomorrow = (today + timedelta(days=1)).isoformat()

    # ── 1. Analyze signals ────────────────────────────────────────────────────
    signals = await analyze(user_id, sb)

    # ── 2. Determine priority ─────────────────────────────────────────────────
    priority = prioritize(signals)

    # ── 3. Curriculum progression ─────────────────────────────────────────────
    profile = (
        sb.table("users")
        .select("layoff_date")
        .eq("id", user_id)
        .single()
        .execute()
    ).data or {}
    days_since_layoff = 0
    if profile.get("layoff_date"):
        days_since_layoff = (today - date.fromisoformat(profile["layoff_date"])).days

    past_plans = (
        sb.table("plans")
        .select("plan_json")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .limit(30)
        .execute()
    ).data or []
    completed_topics = list({
        p["plan_json"]["leetcode_topic"]
        for p in past_plans
        if p.get("plan_json") and p["plan_json"].get("leetcode_topic")
    })
    next_lc = _get_next_leetcode_topic(completed_topics)
    behavioral = _get_behavioral_focus(days_since_layoff)

    # ── 4. Build time-blocked schedule ───────────────────────────────────────
    schedule = build_schedule(priority, signals, next_lc, behavioral)
    coach_note = build_coach_note(signals, priority)

    # ── 5. Compose plan_json ──────────────────────────────────────────────────
    targets = priority["adjusted_targets"]
    plan_json = {
        "date": tomorrow,
        "priority_mode": priority["priority_mode"],
        "mode_reason": priority["mode_reason"],
        "job_apps": targets.get("job_apps", 8),
        "networking": targets.get("networking", 5),
        "leetcode_problems": targets.get("leetcode_problems", 2),
        "leetcode_topic": next_lc["topic"],
        "leetcode_suggested": next_lc["problems"][:targets.get("leetcode_problems", 2)],
        "behavioral_focus": behavioral,
        "system_design": targets.get("system_design", 1),
        "coach_note": coach_note,
    }

    # ── 6. Save to plans table ────────────────────────────────────────────────
    plan_row = sb.table("plans").insert({
        "user_id": user_id,
        "date": tomorrow,
        "coach_note": coach_note,
        "plan_json": plan_json,
        "schedule": schedule,
        "priority_mode": priority["priority_mode"],
        "signals": signals,
    }).execute()
    plan_id = plan_row.data[0]["id"]

    # ── 7. Update goal_plan.goal_stratergy with current daily plan ────────────
    latest_goal = (
        sb.table("goal_plan")
        .select("id, goal_stratergy")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    ).data
    if latest_goal:
        existing = latest_goal[0].get("goal_stratergy") or {}
        existing["current_daily_plan"] = plan_json
        sb.table("goal_plan").update({"goal_stratergy": existing}).eq("id", latest_goal[0]["id"]).execute()

    print(f"[DAILY PLAN] user={user_id} | mode={priority['priority_mode']} | lc={next_lc['topic']}")
    return {"plan_id": plan_id, "plan": plan_json, "schedule": schedule}


# Keep backward compat — plan_worker calls generate_plan
async def aggregate_for_user(user_id: str) -> dict:
    return await build_daily_plan(user_id)
