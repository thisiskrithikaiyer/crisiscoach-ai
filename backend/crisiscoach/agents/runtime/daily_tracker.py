from langchain_core.messages import HumanMessage
"""Daily tracker agent — processes check-in messages and generates empathetic responses."""
import os
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL
from crisiscoach.orchestrator.state import CrisisCoachState

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


async def generate_checkin_response(
    mood_score: int,
    energy_score: int,
    wins: list[str],
    blockers: list[str],
) -> str:
    wins_text = "\n".join(f"- {w}" for w in wins) if wins else "None reported"
    blockers_text = "\n".join(f"- {b}" for b in blockers) if blockers else "None reported"
    user_msg = (
        f"Today's check-in:\n"
        f"Mood: {mood_score}/10, Energy: {energy_score}/10\n"
        f"Wins:\n{wins_text}\n"
        f"Blockers:\n{blockers_text}"
    )
    system = (
        "You are a direct, caring job-loss coach. Acknowledge the user's mood and energy honestly. "
        "Celebrate wins specifically. Name blockers and give one concrete suggestion. "
        "Be warm but brief (under 120 words). Never be generic."
    )
    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=256,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
    )
    return resp.choices[0].message.content


async def run(state: CrisisCoachState) -> dict:
    last_msg = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None
    )
    content = last_msg.content if last_msg else ""
    system = (
        "You are CrisisCoach. The user wants to do their daily check-in. "
        "If they haven't provided scores, ask for mood (1-10) and energy (1-10), wins, and blockers. "
        "If they have, acknowledge warmly and give one targeted piece of advice."
    )
    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=512,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
    )
    return {"response": resp.choices[0].message.content, "sources": []}
