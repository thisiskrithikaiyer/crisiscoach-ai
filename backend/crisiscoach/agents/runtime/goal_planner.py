"""Goal planner agent — builds a personalized 60-day job search strategy after intake."""
import json
from datetime import date, timedelta
from langchain_core.messages import HumanMessage
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL
from crisiscoach.orchestrator.state import CrisisCoachState
from crisiscoach.prompts.loader import load_prompt

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

_EXTRACTION_PROMPT = """
Extract the goal plan from the assistant message below into this exact JSON schema.
Return ONLY valid JSON — no markdown, no explanation.

{
  "mode": "CRISIS | URGENT | STANDARD | STRATEGIC",
  "resume_score": <int 1-10 or null>,
  "linkedin_score": <int 1-10 or null>,
  "role_targets": {
    "stretch": "<role name or null>",
    "realistic": "<role name or null>",
    "safety": "<role name or null>"
  },
  "daily_targets": {
    "applications": <int>,
    "networking_messages": <int>,
    "linkedin_connects": <int>,
    "leetcode_problems": <int>
  },
  "weekly_milestones": [
    {"week": "1-2", "goal": "<summary>"},
    {"week": "3-4", "goal": "<summary>"},
    {"week": "5-6", "goal": "<summary>"},
    {"week": "7-8", "goal": "<summary>"}
  ],
  "leetcode_tier": "fundamentals | building | standard | advanced",
  "technical_focus": "<one sentence summary of technical practice focus>"
}

Assistant message:
"""


def _build_system(state: CrisisCoachState) -> str:
    base = load_prompt("goal_planner.txt")
    snippets = []
    if state.get("days_since_layoff") is not None:
        snippets.append(f"Days since layoff: {state['days_since_layoff']}")
    if state.get("runway_weeks") is not None:
        snippets.append(f"Financial runway: ~{state['runway_weeks']} weeks")
    if state.get("visa_deadline_days") is not None:
        snippets.append(f"Visa deadline: {state['visa_deadline_days']} days away")
    if state.get("mood_score") is not None:
        snippets.append(f"Last mood score: {state['mood_score']}/10")
    if state.get("energy_score") is not None:
        snippets.append(f"Last energy score: {state['energy_score']}/10")
    if state.get("open_tasks") is not None:
        snippets.append(f"Open tasks from plan: {state['open_tasks']}")
    if state.get("resume_text"):
        snippets.append(f"\nRESUME TEXT:\n{state['resume_text']}")
    if state.get("linkedin_text"):
        snippets.append(f"\nLINKEDIN PROFILE TEXT:\n{state['linkedin_text']}")

    tracking = state.get("tracking_summary")
    if tracking and tracking.get("revision_mode"):
        t = tracking
        act = t.get("activity", {})
        dev = t.get("deviation", {})
        ts = t.get("task_stats", {})

        snippets.append("\n--- REVISION DATA (pre-computed from DB — do not fabricate any number) ---")
        snippets.append("REVISION_MODE: true")
        snippets.append(f"Current day of search: Day {t.get('current_day')}")
        snippets.append(f"Avg mood: {t.get('avg_mood')}/10 | Avg energy: {t.get('avg_energy')}/10")

        # Task completion
        if ts.get("completion_rate") is not None:
            snippets.append(f"Task completion: {ts['completion_rate']}% ({ts['completed']}/{ts['total']})")
        if ts.get("by_category"):
            snippets.append("By category: " + " | ".join(
                f"{cat}: {v['rate']}% ({v['completed']}/{v['total']})"
                for cat, v in ts["by_category"].items()
            ))

        # Activity vs goal deviation
        if dev:
            for key, label in [("apps", "Apps"), ("networking", "Networking"), ("leetcode", "Leetcode")]:
                if key in dev and dev[key]["deviation_pct"] is not None:
                    d = dev[key]
                    snippets.append(f"{label}: {d['actual']} done (target {d['target']}, {d['deviation_pct']:+d}%)")
        snippets.append(f"System design sessions done: {act.get('total_system_design', 0)}")

        # Interview stats
        snippets.append(f"Interviews completed: {act.get('total_interviews_completed', 0)}")
        snippets.append(f"Interviews passed: {act.get('total_interviews_passed', 0)} | Failed: {act.get('total_interviews_failed', 0)}")
        if act.get("pass_rate") is not None:
            snippets.append(f"Interview pass rate: {act['pass_rate']}%")
        if act.get("top_interview_topics"):
            snippets.append(f"Top interview topics asked: {', '.join(act['top_interview_topics'])}")
        if act.get("days_since_interview") is not None:
            snippets.append(f"Days since last interview: {act['days_since_interview']}")
        if t.get("no_interview_rescore"):
            snippets.append("NO_INTERVIEW_FLAG: true — 14+ days with no interview. Resume/LinkedIn rescore required.")

        # Recurring blockers
        if t.get("recurring_blockers"):
            snippets.append(f"Recurring blockers: {', '.join(t['recurring_blockers'])}")

        # Daily log
        if t.get("daily_log"):
            snippets.append("\nDaily activity log (oldest → newest):")
            for day in t["daily_log"]:
                topics = ", ".join(day["topics"]) if day.get("topics") else "—"
                snippets.append(
                    f"  {day['date']} | mood {day.get('mood','?')} energy {day.get('energy','?')} "
                    f"| apps {day.get('apps',0)} net {day.get('networking',0)} "
                    f"| lc {day.get('leetcode_done',0)} sd {day.get('system_design_done',0)} "
                    f"| interviews {day.get('interviews_completed',0)} "
                    f"(pass {day.get('interviews_passed',0)} fail {day.get('interviews_failed',0)}) "
                    f"| topics: {topics}"
                )

    return base + ("\n\nUser context:\n" + "\n".join(snippets) if snippets else "")


def _has_profile(state: CrisisCoachState) -> bool:
    return bool(state.get("resume_text") or state.get("linkedin_text"))


def _save_flags(state: CrisisCoachState) -> None:
    user_id = state.get("user_id")
    if not user_id:
        return
    updates = {}
    if state.get("runway_weeks") is not None:
        updates["runway_weeks"] = state["runway_weeks"]
    if state.get("visa_deadline_days") is not None:
        deadline = date.today() + timedelta(days=state["visa_deadline_days"])
        updates["visa_deadline"] = deadline.isoformat()
    if state.get("days_since_layoff") is not None:
        layoff_date = date.today() - timedelta(days=state["days_since_layoff"])
        updates["layoff_date"] = layoff_date.isoformat()
    if not updates:
        return
    try:
        from crisiscoach.db.supabase import get_client
        get_client().table("users").update(updates).eq("id", user_id).execute()
    except Exception:
        pass  # non-blocking — don't fail the response over a DB write


def _extract_and_save_plan(user_id: str, response_text: str, revision_analytics: dict | None = None) -> None:
    """Extract structured JSON from the plan text and persist to goal_plan."""
    try:
        extraction = _client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=1024,
            temperature=0,
            messages=[{"role": "user", "content": _EXTRACTION_PROMPT + response_text}],
        )
        raw = extraction.choices[0].message.content.strip()
        plan_json = json.loads(raw)
    except Exception:
        return

    try:
        from crisiscoach.db.supabase import get_client
        row: dict = {
            "user_id": user_id,
            "date": date.today().isoformat(),
            "goal_stratergy": plan_json,
        }
        if revision_analytics:
            row["revision_analytics"] = revision_analytics
        get_client().table("goal_plan").insert(row).execute()
    except Exception:
        pass


async def run(state: CrisisCoachState) -> dict:
    _save_flags(state)

    if not _has_profile(state):
        return {
            "response": (
                "Before I build your strategy, I need to see what you're working with.\n\n"
                "Go to the dashboard and paste:\n"
                "1. Your resume text\n"
                "2. Your LinkedIn profile text (About + Experience sections)\n\n"
                "Once that's in, I'll score both, tell you what roles to target, and build your full plan around what you actually have."
                "\nCHIPS: [\"Done, I've added them\", \"Skip for now\"]"
            ),
            "sources": [],
        }

    system = _build_system(state)
    history = [
        {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content}
        for m in state["messages"]
    ]
    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=2048,
        messages=[{"role": "system", "content": system}, *history],
    )
    response_text = resp.choices[0].message.content

    user_id = state.get("user_id")
    tracking = state.get("tracking_summary") or {}

    # Detect commitment confirmation from the user's last message
    last_human = next((m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None)
    last_human_text = (last_human.content.strip().lower() if last_human else "")
    _COMMIT_SIGNALS = ("commit", "yes", "let's do it", "lets do it", "sounds good", "i'm in", "im in", "deal", "go for it", "agreed")
    committed = any(sig in last_human_text for sig in _COMMIT_SIGNALS)

    # Only save the goal plan when the LLM response contains an actual plan (has milestones/targets)
    # Guard: the response must look like a real plan presentation, not just a question/clarification
    _PLAN_SIGNALS = ("week 1", "week 2", "daily target", "applications per day", "leetcode", "milestone", "strategy", "plan")
    is_plan_response = any(sig in response_text.lower() for sig in _PLAN_SIGNALS)

    if user_id and is_plan_response:
        revision_analytics = {
            "activity": tracking.get("activity"),
            "deviation": tracking.get("deviation"),
            "task_stats": tracking.get("task_stats"),
            "avg_mood": tracking.get("avg_mood"),
            "avg_energy": tracking.get("avg_energy"),
            "no_interview_rescore": tracking.get("no_interview_rescore"),
        } if tracking.get("revision_mode") else None
        _extract_and_save_plan(user_id, response_text, revision_analytics)

    # Stamp commitment + transition to active phase only after user explicitly commits
    if user_id and committed:
        try:
            from crisiscoach.db.supabase import get_client
            sb = get_client()
            latest = (
                sb.table("goal_plan")
                .select("id")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            ).data
            if latest:
                sb.table("goal_plan").update({
                    "goal_committed_at": date.today().isoformat(),
                    "next_revision_date": (date.today() + timedelta(days=10)).isoformat(),
                }).eq("id", latest[0]["id"]).execute()
            # Transition to active phase
            sb.table("users").update({"phase": "active"}).eq("id", user_id).execute()
        except Exception:
            pass

        # Launch daily plan builder in background so today's plan is ready immediately
        try:
            import asyncio
            from crisiscoach.agents.background.daily_check import build_daily_plan
            asyncio.get_event_loop().create_task(build_daily_plan(user_id))
        except Exception:
            pass

    new_phase = "active" if committed else state.get("phase", "goal_setup")
    return {"response": response_text, "sources": [], "phase": new_phase}
