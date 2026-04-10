"""Assembles minimal user context for the current request without blocking the response."""
from __future__ import annotations
from datetime import date, timedelta
from crisiscoach.orchestrator.state import CrisisCoachState

REVISION_MODE_MIN_DAYS = 10
NO_INTERVIEW_RESCORE_DAYS = 14

# Only these agents use resume/LinkedIn text and tracking data
_PROFILE_AGENTS = {"goal_planner"}


def _compute_deviation(actual: int, target: int) -> dict:
    if target == 0:
        return {"actual": actual, "target": target, "deviation_pct": None}
    dev = round((actual - target) / target * 100)
    return {"actual": actual, "target": target, "deviation_pct": dev}


async def _fetch_tracking_summary(sb, user_id: str, days_since_layoff: int | None) -> dict:
    try:
        # Last 14 check-ins
        checkin_rows = (
            sb.table("checkins")
            .select("mood_score, energy_score, wins, blockers, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(14)
            .execute()
        ).data or []

        # Task completion over last 14 days
        plan_rows = (
            sb.table("plans")
            .select("id, date")
            .eq("user_id", user_id)
            .order("date", desc=True)
            .limit(14)
            .execute()
        ).data or []

        task_stats: dict = {"total": 0, "completed": 0, "completion_rate": None, "by_category": {}}
        if plan_rows:
            plan_ids = [p["id"] for p in plan_rows]
            task_rows = (
                sb.table("plan_tasks")
                .select("completed, category")
                .in_("plan_id", plan_ids)
                .execute()
            ).data or []
            task_stats["total"] = len(task_rows)
            task_stats["completed"] = sum(1 for t in task_rows if t.get("completed"))
            if task_stats["total"] > 0:
                task_stats["completion_rate"] = round(
                    task_stats["completed"] / task_stats["total"] * 100
                )
            by_cat: dict[str, dict] = {}
            for t in task_rows:
                cat = t.get("category", "other")
                by_cat.setdefault(cat, {"total": 0, "completed": 0})
                by_cat[cat]["total"] += 1
                if t.get("completed"):
                    by_cat[cat]["completed"] += 1
            task_stats["by_category"] = {
                cat: {
                    "rate": round(v["completed"] / v["total"] * 100) if v["total"] else 0,
                    **v,
                }
                for cat, v in by_cat.items()
            }

        # Daily activity logs (apps, networking, interviews)
        log_rows = (
            sb.table("daily_log")
            .select("date, apps_done, networking_done, interviews_scheduled, "
                    "interviews_completed, interviews_passed, interviews_failed, "
                    "interview_topics, leetcode_done, system_design_done")
            .eq("user_id", user_id)
            .order("date", desc=True)
            .limit(14)
            .execute()
        ).data or []
        log_rows_asc = list(reversed(log_rows))

        # Aggregate activity totals
        total_apps = sum(r.get("apps_done", 0) for r in log_rows)
        total_networking = sum(r.get("networking_done", 0) for r in log_rows)
        total_interviews_completed = sum(r.get("interviews_completed", 0) for r in log_rows)
        total_interviews_passed = sum(r.get("interviews_passed", 0) for r in log_rows)
        total_interviews_failed = sum(r.get("interviews_failed", 0) for r in log_rows)
        total_leetcode = sum(r.get("leetcode_done", 0) for r in log_rows)
        total_system_design = sum(r.get("system_design_done", 0) for r in log_rows)
        all_topics = [t for r in log_rows for t in (r.get("interview_topics") or [])]
        topic_freq: dict[str, int] = {}
        for t in all_topics:
            topic_freq[t] = topic_freq.get(t, 0) + 1
        top_topics = sorted(topic_freq, key=lambda k: -topic_freq[k])[:5]

        # Days since last interview
        days_since_interview = None
        for r in log_rows:  # already desc
            if r.get("interviews_completed", 0) > 0:
                last_interview_date = date.fromisoformat(r["date"])
                days_since_interview = (date.today() - last_interview_date).days
                break
        no_interview_rescore = (
            days_since_interview is None or days_since_interview >= NO_INTERVIEW_RESCORE_DAYS
        ) and (days_since_layoff or 0) >= NO_INTERVIEW_RESCORE_DAYS

        # Latest goal targets for deviation calc
        goal_row = (
            sb.table("goal_plan")
            .select("goal_stratergy")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        ).data
        goal_targets = (goal_row[0].get("goal_stratergy", {}) or {}).get("daily_targets", {}) if goal_row else {}

        num_days = len(log_rows) or 1
        deviation: dict = {}
        if goal_targets:
            app_target_total = goal_targets.get("applications", 0) * num_days
            net_target_total = goal_targets.get("networking_messages", 0) * num_days
            lc_target_total = goal_targets.get("leetcode_problems", 0) * num_days
            deviation = {
                "apps": _compute_deviation(total_apps, app_target_total),
                "networking": _compute_deviation(total_networking, net_target_total),
                "leetcode": _compute_deviation(total_leetcode, lc_target_total),
            }

        # Revision mode gate: check-ins must span 10+ days
        revision_mode = False
        if checkin_rows and len(checkin_rows) >= 2:
            oldest = date.fromisoformat(checkin_rows[-1]["created_at"][:10])
            newest = date.fromisoformat(checkin_rows[0]["created_at"][:10])
            if (newest - oldest).days >= REVISION_MODE_MIN_DAYS:
                revision_mode = True

        if not revision_mode:
            return {"current_day": days_since_layoff, "revision_mode": False}

        avg_mood = round(sum(c["mood_score"] for c in checkin_rows) / len(checkin_rows), 1)
        avg_energy = round(sum(c["energy_score"] for c in checkin_rows) / len(checkin_rows), 1)
        all_blockers = [b for c in checkin_rows for b in (c.get("blockers") or [])]

        daily_log_summary = [
            {
                "date": r["date"],
                "mood": next((c["mood_score"] for c in checkin_rows if c["created_at"][:10] == r["date"]), None),
                "energy": next((c["energy_score"] for c in checkin_rows if c["created_at"][:10] == r["date"]), None),
                "apps": r.get("apps_done", 0),
                "networking": r.get("networking_done", 0),
                "interviews_completed": r.get("interviews_completed", 0),
                "interviews_passed": r.get("interviews_passed", 0),
                "interviews_failed": r.get("interviews_failed", 0),
                "topics": r.get("interview_topics") or [],
                "leetcode_done": r.get("leetcode_done", 0),
                "system_design_done": r.get("system_design_done", 0),
            }
            for r in log_rows_asc
        ]

        return {
            "revision_mode": True,
            "current_day": days_since_layoff,
            "checkin_count": len(checkin_rows),
            "avg_mood": avg_mood,
            "avg_energy": avg_energy,
            "recurring_blockers": list(dict.fromkeys(all_blockers))[:5],
            "task_stats": task_stats,
            "activity": {
                "total_apps": total_apps,
                "total_networking": total_networking,
                "total_interviews_completed": total_interviews_completed,
                "total_interviews_passed": total_interviews_passed,
                "total_interviews_failed": total_interviews_failed,
                "pass_rate": round(total_interviews_passed / total_interviews_completed * 100)
                             if total_interviews_completed > 0 else None,
                "top_interview_topics": top_topics,
                "days_since_interview": days_since_interview,
                "total_leetcode": total_leetcode,
                "total_system_design": total_system_design,
            },
            "deviation": deviation,
            "no_interview_rescore": no_interview_rescore,
            "daily_log": daily_log_summary,
        }
    except Exception:
        return {}


async def build_context(state: CrisisCoachState, intent: str = "") -> dict:
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

        # User profile — only fetch heavy text fields when the agent needs them
        needs_profile = intent in _PROFILE_AGENTS
        # phase + intake_complete always fetched — router needs them on every request
        profile_cols = "layoff_date, visa_deadline, runway_weeks, open_tasks, intake_complete, phase"
        if needs_profile:
            profile_cols += ", resume_text, linkedin_text, role, leetcode_level"

        profile_row = (
            sb.table("users")
            .select(profile_cols)
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

        tracking_summary = None
        if needs_profile:
            tracking_summary = await _fetch_tracking_summary(sb, user_id, days_since_layoff)

        return {
            "days_since_layoff": days_since_layoff,
            "visa_deadline_days": visa_deadline_days,
            "runway_weeks": profile.get("runway_weeks"),
            "mood_score": checkin.get("mood_score"),
            "energy_score": checkin.get("energy_score"),
            "intake_complete": bool(profile.get("intake_complete", False)),
            "phase": profile.get("phase", "intake"),
            "open_tasks": profile.get("open_tasks"),
            "resume_text": profile.get("resume_text"),
            "linkedin_text": profile.get("linkedin_text"),
            "tracking_summary": tracking_summary,
        }
    except Exception:
        return {}
