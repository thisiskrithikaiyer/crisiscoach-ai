"""Orchestrator node — classifies intent, enriches context, delegates to agent."""
from crisiscoach.orchestrator.state import CrisisCoachState
from crisiscoach.orchestrator.router import classify_intent
from crisiscoach.orchestrator.context_builder import build_context


AGENT_MAP = {
    "intake":         "crisiscoach.agents.runtime.intake",
    "checkin":        "crisiscoach.agents.runtime.daily_tracker",
    "plan":           "crisiscoach.agents.runtime.accountability",
    "accountability": "crisiscoach.agents.runtime.accountability",
    "mental_health":  "crisiscoach.agents.runtime.mental_health_check",
    "chat":           "crisiscoach.agents.runtime.intake",  # intake handles general chat too
}


async def orchestrator_node(state: CrisisCoachState) -> dict:
    """LangGraph node: route → enrich context → return updated state."""
    intent = classify_intent(state)
    ctx = await build_context(state)

    return {**ctx, "intent": intent, "agent": AGENT_MAP.get(intent, AGENT_MAP["chat"])}
