"""Intent classification — decides which agent handles the current message."""
import json
from langchain_core.messages import HumanMessage
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL
from crisiscoach.orchestrator.state import CrisisCoachState

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

INTENTS = {
    "checkin":        "User wants to log how they feel today (mood, energy, wins, blockers).",
    "plan":           "User wants to see or discuss their daily/weekly action plan.",
    "accountability": "User is reporting progress on tasks or asking to be held accountable.",
    "mental_health":  "User expresses emotional distress, burnout, anxiety, or crisis signals.",
    "goal_planner":   "User wants to revise or revisit their job search strategy or 60-day plan.",
    "chat":           "General question or conversation that doesn't fit above.",
}

_SYSTEM = (
    "You are a routing classifier for CrisisCoach AI. "
    "Given the last user message, output a single JSON object: "
    '{"intent": "<one of: checkin, plan, accountability, mental_health, goal_planner, chat>"}. '
    "No explanation, only JSON."
)

ONBOARDING_INTAKE_LABELS = {
    "lost my job recently",
    "financial pressure",
    "career uncertainty",
    "relationship difficulties",
    "just feeling lost",
}

INTAKE_COMPLETION_PHRASES = {
    "yes, let's go", "yes lets go", "yes, let's go!", "let's go", "yes let's go"
}

MENTAL_HEALTH_SIGNALS = {
    "want to die", "kill myself", "end it", "can't go on", "hopeless",
    "suicidal", "no point", "give up", "breaking down",
}


def _is_mental_health_crisis(text: str) -> bool:
    return any(signal in text for signal in MENTAL_HEALTH_SIGNALS)


def classify_intent(state: CrisisCoachState) -> str:
    phase = state.get("phase", "intake")
    last_msg = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )
    if last_msg is None:
        return "intake" if phase == "intake" else "chat"

    text = last_msg.content.strip().lower()

    # Mental health crisis always breaks through any phase gate
    if _is_mental_health_crisis(text):
        return "mental_health"

    # ── PHASE: intake ─────────────────────────────────────────────────────────
    if phase == "intake":
        if text in ONBOARDING_INTAKE_LABELS:
            return "intake"
        # User confirmed goal → intake agent will handle response AND set phase=goal_setup
        if text in INTAKE_COMPLETION_PHRASES:
            return "intake"   # keep in intake — agent sets phase, THEN goal_planner takes over next turn
        return "intake"

    # ── PHASE: goal_setup ─────────────────────────────────────────────────────
    if phase == "goal_setup":
        return "goal_planner"

    # ── PHASE: active — LLM routing ───────────────────────────────────────────
    intent_list = "\n".join(f"- {k}: {v}" for k, v in INTENTS.items())
    try:
        resp = _client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=64,
            temperature=0,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": f"Intents:\n{intent_list}\n\nUser message: {last_msg.content}"},
            ],
        )
        data = json.loads(resp.choices[0].message.content.strip())
        intent = data.get("intent", "chat")
        return intent if intent in INTENTS else "chat"
    except Exception:
        return "chat"
