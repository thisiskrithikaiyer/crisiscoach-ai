"""Intake agent — first-contact for new users and general coaching chat."""
import os
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL
from crisiscoach.orchestrator.state import CrisisCoachState

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


def _build_system(state: CrisisCoachState) -> str:
    with open(os.path.join(os.path.dirname(__file__), "../../prompts/intake.txt")) as f:
        base = f.read()
    snippets = []
    if state.get("days_since_layoff") is not None:
        snippets.append(f"Days since layoff: {state['days_since_layoff']}")
    if state.get("runway_weeks") is not None:
        snippets.append(f"Financial runway: ~{state['runway_weeks']} weeks")
    if state.get("visa_deadline_days") is not None:
        snippets.append(f"Visa deadline: {state['visa_deadline_days']} days away")
    return base + ("\n\nUser context:\n" + "\n".join(snippets) if snippets else "")


async def run(state: CrisisCoachState) -> dict:
    system = _build_system(state)
    history = [
        {"role": "user" if getattr(m, "type", "") == "human" else "assistant", "content": m.content}
        for m in state["messages"]
    ]
    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=1024,
        messages=[{"role": "system", "content": system}, *history],
    )
    return {"response": resp.choices[0].message.content, "sources": []}
