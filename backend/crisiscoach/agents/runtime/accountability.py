"""Accountability agent — reviews task progress and adjusts the plan."""
import os
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL
from crisiscoach.orchestrator.state import CrisisCoachState

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


async def run(state: CrisisCoachState) -> dict:
    last_msg = next(
        (m for m in reversed(state["messages"]) if getattr(m, "type", "") == "human"), None
    )
    content = last_msg.content if last_msg else ""

    open_tasks = state.get("open_tasks")
    task_context = f"The user has {open_tasks} open tasks from their plan." if open_tasks else ""

    system = (
        "You are a direct accountability coach for someone who was recently laid off. "
        f"{task_context} "
        "When the user reports progress: celebrate specifics, probe for blockers, "
        "and suggest a concrete next action. When they're stuck: name the obstacle clearly, "
        "offer one small step forward. Do not moralize. Keep it under 150 words."
    )
    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=512,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
    )
    return {"response": resp.choices[0].message.content, "sources": []}
