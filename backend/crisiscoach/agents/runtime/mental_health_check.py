"""Mental health check agent — crisis-aware, empathetic, resource-linking."""
import os
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL
from crisiscoach.orchestrator.state import CrisisCoachState

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

CRISIS_KEYWORDS = {"suicid", "end my life", "don't want to be here", "kill myself", "self-harm"}

SAFETY_RESPONSE = (
    "I hear you, and I'm glad you're talking to me right now. "
    "What you're feeling matters. Please reach out to the 988 Suicide & Crisis Lifeline "
    "by calling or texting 988 — they're available 24/7. "
    "If you're in immediate danger, call 911. I'm here with you."
)


def _is_crisis(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in CRISIS_KEYWORDS)


async def run(state: CrisisCoachState) -> dict:
    last_msg = next(
        (m for m in reversed(state["messages"]) if getattr(m, "type", "") == "human"), None
    )
    content = last_msg.content if last_msg else ""

    if _is_crisis(content):
        return {"response": SAFETY_RESPONSE, "sources": ["https://988lifeline.org"]}

    mood = state.get("mood_score")
    mood_context = f"Their last mood score was {mood}/10." if mood else ""

    system = (
        "You are a compassionate mental health support companion for someone navigating job loss. "
        f"{mood_context} "
        "Use active listening. Validate feelings without judgment. "
        "You are NOT a therapist — acknowledge this if relevant and recommend professional help when appropriate. "
        "If burnout or prolonged distress is present, name it gently. "
        "Keep response warm and under 200 words."
    )
    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=512,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
    )
    return {"response": resp.choices[0].message.content, "sources": []}
