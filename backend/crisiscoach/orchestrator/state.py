from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class CrisisCoachState(TypedDict):
    # Conversation
    messages: Annotated[list, add_messages]
    user_id: str

    # Routing
    intent: str          # classified intent: chat | intake | checkin | plan | accountability
    agent: str           # which agent handled this turn

    # User snapshot (populated by context_builder)
    days_since_layoff: int | None
    visa_deadline_days: int | None
    runway_weeks: int | None
    mood_score: int | None        # 1-10 from last check-in
    energy_score: int | None      # 1-10 from last check-in
    open_tasks: int | None        # uncompleted plan items

    # Response
    response: str
    sources: list[str]            # citations from RAG
