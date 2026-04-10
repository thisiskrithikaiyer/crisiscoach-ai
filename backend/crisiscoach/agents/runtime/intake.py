from langchain_core.messages import HumanMessage
"""Intake agent — collects all required fields before handing off to goal planner."""
import json
from datetime import date, timedelta
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL
from crisiscoach.orchestrator.state import CrisisCoachState
from crisiscoach.orchestrator.state_prompt import state_to_prompt
from crisiscoach.prompts.loader import load_prompt

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

REQUIRED_FIELDS = {"role", "timeline", "runway", "leetcode_level"}

# Maps extracted timeline string → days since layoff
TIMELINE_TO_DAYS = {
    "just_happened": 1,
    "1_2_weeks":     10,
    "1_month":       30,
    "2_3_months":    75,
}

# Maps extracted runway string → weeks of runway
RUNWAY_TO_WEEKS = {
    "lt_4_weeks": 3,
    "1_2_months": 6,
    "3_6_months": 18,
    "6_plus":     30,
    "not_sure":   None,
}

_FIELD_EXTRACT_PROMPT = """
Extract what intake fields have been confirmed so far from this conversation.
Return ONLY valid JSON. Use null if not yet collected.

{
  "role": "SWE | MLE | AI Engineer | Data Engineer | Other | null",
  "timeline": "just_happened | 1_2_weeks | 1_month | 2_3_months | null",
  "visa_pressure": true | false | null,
  "visa_days": <int days until visa expires, or null>,
  "runway": "lt_4_weeks | 1_2_months | 3_6_months | 6_plus | not_sure | null",
  "leetcode_level": "cant_do_two_sum | shaky_mediums | comfortable_mediums | can_do_hards | null",
  "goal_confirmed": true | false
}

Conversation:
"""


def _extract_fields(history: list[dict]) -> dict:
    try:
        convo = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history[-14:])
        resp = _client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=256,
            temperature=0,
            messages=[{"role": "user", "content": _FIELD_EXTRACT_PROMPT + convo}],
        )
        return json.loads(resp.choices[0].message.content.strip())
    except Exception:
        return {}


def _derive_deadline_state(fields: dict, state: CrisisCoachState) -> dict:
    days_since = TIMELINE_TO_DAYS.get(fields.get("timeline", ""), state.get("days_since"))

    candidates = []
    runway_weeks = RUNWAY_TO_WEEKS.get(fields.get("runway", ""))
    if runway_weeks is not None:
        candidates.append(runway_weeks * 7)
    if fields.get("visa_pressure") and fields.get("visa_days"):
        candidates.append(int(fields["visa_days"]))
    days_left = min(candidates) if candidates else state.get("days_left")

    existing_skills = state.get("tracking_skills") or {}
    leetcode_level = fields.get("leetcode_level")
    tracking_skills = {**existing_skills, "leetcode_level": leetcode_level} if leetcode_level else existing_skills or None

    return {"days_since": days_since, "days_left": days_left, "tracking_skills": tracking_skills}


def _all_fields_collected(fields: dict) -> bool:
    return all(fields.get(f) is not None for f in REQUIRED_FIELDS)


def _persist_intake_fields(user_id: str, fields: dict) -> None:
    """Save whatever intake fields are known so far to the users table."""
    updates: dict = {}

    if fields.get("role"):
        updates["role"] = fields["role"]

    if fields.get("timeline"):
        days = TIMELINE_TO_DAYS.get(fields["timeline"])
        if days is not None:
            layoff_date = date.today() - timedelta(days=days)
            updates["layoff_date"] = layoff_date.isoformat()

    if fields.get("runway") is not None:
        weeks = RUNWAY_TO_WEEKS.get(fields["runway"])
        if weeks is not None:
            updates["runway_weeks"] = weeks

    if fields.get("visa_pressure") is True and fields.get("visa_days"):
        visa_deadline = date.today() + timedelta(days=int(fields["visa_days"]))
        updates["visa_deadline"] = visa_deadline.isoformat()

    if fields.get("leetcode_level"):
        updates["leetcode_level"] = fields["leetcode_level"]

    if not updates:
        return

    try:
        from crisiscoach.db.supabase import get_client
        get_client().table("users").update(updates).eq("id", user_id).execute()
        print(f"[INTAKE] Saved to DB: {list(updates.keys())}")
    except Exception as e:
        print(f"[INTAKE] DB save failed: {e}")


def _build_system(state: CrisisCoachState, fields: dict) -> str:
    base = load_prompt("intake.txt")
    snippets = []

    # Inject already-known values so LLM doesn't re-ask
    if fields.get("role"):
        snippets.append(f"Role already confirmed: {fields['role']}")
    if fields.get("timeline"):
        snippets.append(f"Timeline already confirmed: {fields['timeline']}")
    if fields.get("runway"):
        snippets.append(f"Runway already confirmed: {fields['runway']}")
    if fields.get("leetcode_level"):
        snippets.append(f"Leetcode level already confirmed: {fields['leetcode_level']}")
    snippets.append(state_to_prompt(state))

    missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
    if missing:
        snippets.append(f"\nSTILL NEED TO COLLECT: {', '.join(missing)}")
        snippets.append("Do NOT propose the 60-day goal until all fields above are collected.")
    else:
        snippets.append("\nAll required fields collected. You may now propose the 60-day goal.")

    return base + ("\n\nUser context:\n" + "\n".join(snippets) if snippets else "")


async def run(state: CrisisCoachState) -> dict:
    history = [
        {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content}
        for m in state["messages"]
    ]

    fields = _extract_fields(history)
    all_done = _all_fields_collected(fields)
    goal_confirmed = bool(fields.get("goal_confirmed"))

    user_id = state.get("user_id")

    # Persist whatever is known so far on every turn — not just at completion
    if user_id:
        _persist_intake_fields(user_id, fields)

    system = _build_system(state, fields)
    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=1024,
        messages=[{"role": "system", "content": system}, *history],
    )
    response_text = resp.choices[0].message.content

    intake_done = all_done and goal_confirmed
    new_phase = "goal_planner" if intake_done else "intake"

    if intake_done and user_id:
        try:
            from crisiscoach.db.supabase import get_client
            get_client().table("users").update({
                "intake_complete": True,
                "phase": "goal_setup",
            }).eq("id", user_id).execute()
        except Exception:
            pass

    return {
        "response": response_text,
        "sources": [],
        "intake_complete": intake_done,
        "phase": new_phase,
        **_derive_deadline_state(fields, state),
    }
