"""
Supervisor agent — the central brain of CrisisCoach.
Reads phase, conversation history, and user context to decide which agent runs next.
Replaces the rule-based router with an LLM that reasons about handoffs.
"""
import json
from datetime import date
from langchain_core.messages import HumanMessage
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL
from crisiscoach.orchestrator.state import CrisisCoachState
from crisiscoach.orchestrator.state_prompt import state_to_prompt

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

AGENTS = {
    "intake": (
        "Runs when phase is intake. Handles only new users. Collects all the information from the user, "
        "Once all required information is registered change phase=goal_planner."
    ),
    "goal_planner": (
        "Builds or revises the job search strategy for the deadline. Runs when phase=goal_planner "
        "or when user explicitly wants to revisit their plan."
    ),
    "checkin": (
        "User is logging how today went: mood, energy, wins, blockers, prep done, applications sent, interviews completed."
    ),
    "accountability": (
        "User wants to review planned vs actual, be held to commitments, or is showing drift: "
        "missed days, low motivation, spiraling, or wasting time."
    ),
    "mental_health": (
        "User is expressing extreme distress, burnout, hopelessness, or crisis signals like suicidal ideation or self-harm. "
        "ALWAYS takes priority — route here if ANY distress signal is present."
    ),
    "profile_builder": (
        "User wants help improving their resume or LinkedIn profile: rewriting sections, fixing formatting, "
        "strengthening bullet points, or tailoring it to a role."
    ),
    "technical_prep": (
        "User wants to practice or get help with technical interview topics: DSA, system design, "
        "coding problems, or concept explanations."
    ),
    "mock_prep": (
        "User wants to do a mock interview: behavioral, technical, or role-specific simulation "
        "where the coach acts as the interviewer."
    ),
    "chat": (
        "General questions or conversation that don't fit any other agent."
    ),
}

MENTAL_HEALTH_SIGNALS = {
    "want to die", "kill myself", "end it", "can't go on", "hopeless",
    "suicidal", "no point", "give up", "breaking down",
}

_SUPERVISOR_SYSTEM = """You are the supervisor of CrisisCoach AI — a job-loss coaching app.
Your only job is to decide which specialist agent should handle the user's current message.

Today's date: {today}

Available agents:
{agents}

Phase rules (HARD — never break these):
- phase=intake → ONLY route to "intake". No exceptions except mental_health crisis.
- phase=goal_setup → ONLY route to "goal_planner". No exceptions except mental_health crisis.
- phase=active → route freely based on the user's message.

Mental health override: If the user shows ANY crisis signal (hopelessness, self-harm, suicidal ideation), ALWAYS route to "mental_health" regardless of phase.

User context:
{context}

Output a single JSON object. No explanation.
{{"agent": "<agent_name>", "reason": "<one line why>"}}
"""




def _is_crisis(text: str) -> bool:
    return any(signal in text.lower() for signal in MENTAL_HEALTH_SIGNALS)


def decide(state: CrisisCoachState) -> str:
    """Return the agent name to route to."""
    phase = state.get("phase", "intake")

    last_msg = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )
    if last_msg is None:
        return "intake" if phase == "intake" else "chat"

    text = last_msg.content.strip()

    # Hard crisis override
    if _is_crisis(text):
        print("[SUPERVISOR] Crisis signal detected → mental_health")
        return "mental_health"

    # Hard phase locks — no LLM needed
    if phase == "intake":
        return "intake"
    if phase == "goal_setup":
        return "goal_planner"

    # phase=active — ask the LLM supervisor
    agents_desc = "\n".join(f'- "{k}": {v}' for k, v in AGENTS.items())
    context_snippet = state_to_prompt(state)

    # Last 4 messages for context
    recent = state["messages"][-4:]
    convo = "\n".join(
        f"{'USER' if isinstance(m, HumanMessage) else 'COACH'}: {m.content[:200]}"
        for m in recent
    )

    try:
        resp = _client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=80,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": _SUPERVISOR_SYSTEM.format(
                        today=date.today().isoformat(),
                        agents=agents_desc,
                        context=context_snippet,
                    ),
                },
                {
                    "role": "user",
                    "content": f"Recent conversation:\n{convo}\n\nLatest user message: {text}",
                },
            ],
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)
        agent = data.get("agent", "chat")
        reason = data.get("reason", "")
        result = agent if agent in AGENTS else "chat"
        print(f"[SUPERVISOR] phase={phase} | agent={result} | reason={reason}")
        return result
    except Exception as e:
        print(f"[SUPERVISOR] LLM failed, defaulting to chat: {e}")
        return "chat"
