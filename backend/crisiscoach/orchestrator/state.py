from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class CrisisCoachState(TypedDict):
    # Conversation
    messages: Annotated[list, add_messages]
    user_id: str

    # Routing
    intent: str          # classified intent: chat | intake | checkin | plan | accountability
    agent: str           # which agent handled this turn
    intake_complete: bool  # True once the user has confirmed their 60-day goal
    phase: str           # intake | goal_setup | active — gates which agents can run

    # User snapshot (populated by context_builder)
    days_since_layoff: int | None
    visa_deadline_days: int | None
    runway_weeks: int | None
    mood_score: int | None        # 1-10 from last check-in
    energy_score: int | None      # 1-10 from last check-in
    open_tasks: int | None        # uncompleted plan items
    resume_text: str | None       # pasted resume from dashboard
    linkedin_text: str | None     # pasted LinkedIn profile from dashboard
    tracking_summary: dict | None # last 10 days of checkins + task completion (goal_planner only)

    # Response
    response: str
    sources: list[str]            # citations from RAG
