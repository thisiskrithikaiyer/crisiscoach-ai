"""Intent classification — decides which agent handles the current message."""
import json
import os
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL
from crisiscoach.orchestrator.state import CrisisCoachState

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

INTENTS = {
    "intake":          "User is new or describing their layoff situation for the first time.",
    "checkin":         "User wants to log how they feel today (mood, energy, wins, blockers).",
    "plan":            "User wants to see, update, or generate their daily/weekly action plan.",
    "accountability":  "User is reporting progress on tasks or asking to be held accountable.",
    "mental_health":   "User expresses emotional distress, burnout, anxiety, or crisis signals.",
    "chat":            "General conversation, questions, advice-seeking that doesn't fit above.",
}

_SYSTEM = (
    "You are a routing classifier for CrisisCoach AI. "
    "Given the last user message and conversation context, output a single JSON object: "
    '{"intent": "<one of: intake, checkin, plan, accountability, mental_health, chat>"}. '
    "No explanation, only JSON."
)


def classify_intent(state: CrisisCoachState) -> str:
    """Return the best-match intent string for the latest user message."""
    last_msg = next(
        (m for m in reversed(state["messages"]) if getattr(m, "type", None) == "human"),
        None,
    )
    if last_msg is None:
        return "chat"

    intent_list = "\n".join(f"- {k}: {v}" for k, v in INTENTS.items())
    user_content = f"Intents:\n{intent_list}\n\nUser message: {last_msg.content}"

    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=64,
        temperature=0,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_content},
        ],
    )
    raw = resp.choices[0].message.content.strip()
    try:
        data = json.loads(raw)
        intent = data.get("intent", "chat")
        return intent if intent in INTENTS else "chat"
    except (json.JSONDecodeError, KeyError):
        return "chat"
