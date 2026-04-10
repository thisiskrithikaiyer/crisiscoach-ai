"""
Signal Analyzer — reads all user data and computes actionable signals.
Output drives the plan prioritizer.
"""
from datetime import date, timedelta


async def analyze(user_id: str, sb) -> dict:
    today = date.today()

    # ── Last 7 days of checkins ────────────────────────────────────────────────
    checkins = (
        sb.table("checkins")
        .select("mood_score, energy_score, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(7)
        .execute()
    ).data or []

    avg_mood = round(sum(c["mood_score"] for c in checkins) / len(checkins), 1) if checkins else 5.0
    avg_energy = round(sum(c["energy_score"] for c in checkins) / len(checkins), 1) if checkins else 5.0
    burnout_rate = max(0, round((10 - avg_mood + 10 - avg_energy) / 2, 1))  # 0=fine, 10=burned out
    low_energy_days = sum(1 for c in checkins if c["energy_score"] <= 4)

    # ── Last 7 days of activity logs ──────────────────────────────────────────
    logs = (
        sb.table("daily_log")
        .select("date, apps_done, networking_done, leetcode_done, system_design_done, "
                "interviews_completed, interviews_passed, interviews_failed, interview_topics")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .limit(7)
        .execute()
    ).data or []

    total_apps = sum(r.get("apps_done", 0) for r in logs)
    total_interviews = sum(r.get("interviews_completed", 0) for r in logs)
    total_passed = sum(r.get("interviews_passed", 0) for r in logs)
    total_failed = sum(r.get("interviews_failed", 0) for r in logs)
    pass_rate = round(total_passed / total_interviews * 100) if total_interviews > 0 else None

    # Days since last interview
    days_since_interview = None
    for r in logs:
        if r.get("interviews_completed", 0) > 0:
            days_since_interview = (today - date.fromisoformat(r["date"])).days
            break

    # Topics that keep failing
    failed_topics = [t for r in logs for t in (r.get("interview_topics") or [])
                     if r.get("interviews_failed", 0) > 0]

    # ── Goal plan targets ─────────────────────────────────────────────────────
    goal_row = (
        sb.table("goal_plan")
        .select("goal_stratergy")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    ).data
    goal = {}
    if goal_row and goal_row[0].get("goal_stratergy"):
        goal = goal_row[0]["goal_stratergy"]

    daily_targets = goal.get("daily_targets", {})
    app_target = daily_targets.get("applications", 8)
    net_target = daily_targets.get("networking_messages", 5)
    lc_target = daily_targets.get("leetcode_problems", 2)
    resume_score = goal.get("resume_score")
    linkedin_score = goal.get("linkedin_score")
    leetcode_tier = goal.get("leetcode_tier", "standard")

    # ── Derived signals ───────────────────────────────────────────────────────
    too_many_apps_no_callbacks = total_apps >= (app_target * 5) and total_interviews == 0
    interview_failing = pass_rate is not None and pass_rate < 50
    no_interview_14d = days_since_interview is None or days_since_interview >= 14
    resume_weak = resume_score is not None and resume_score < 6
    linkedin_weak = linkedin_score is not None and linkedin_score < 6
    burned_out = burnout_rate >= 6 or low_energy_days >= 3

    # ── Tomorrow's interviews from log (scheduled) ────────────────────────────
    tomorrow = (today + timedelta(days=1)).isoformat()
    tomorrow_log = (
        sb.table("daily_log")
        .select("interviews_scheduled, interview_topics")
        .eq("user_id", user_id)
        .eq("date", tomorrow)
        .limit(1)
        .execute()
    ).data
    interviews_tomorrow = 0
    interview_topics_tomorrow = []
    if tomorrow_log:
        interviews_tomorrow = tomorrow_log[0].get("interviews_scheduled", 0)
        interview_topics_tomorrow = tomorrow_log[0].get("interview_topics") or []

    return {
        "avg_mood": avg_mood,
        "avg_energy": avg_energy,
        "burnout_rate": burnout_rate,
        "burned_out": burned_out,
        "low_energy_days": low_energy_days,
        "total_apps_7d": total_apps,
        "total_interviews_7d": total_interviews,
        "pass_rate": pass_rate,
        "days_since_interview": days_since_interview,
        "failed_topics": list(set(failed_topics))[:5],
        "interviews_tomorrow": interviews_tomorrow,
        "interview_topics_tomorrow": interview_topics_tomorrow,
        "too_many_apps_no_callbacks": too_many_apps_no_callbacks,
        "interview_failing": interview_failing,
        "no_interview_14d": no_interview_14d,
        "resume_weak": resume_weak,
        "linkedin_weak": linkedin_weak,
        "app_target": app_target,
        "net_target": net_target,
        "lc_target": lc_target,
        "leetcode_tier": leetcode_tier,
        "resume_score": resume_score,
        "linkedin_score": linkedin_score,
    }
