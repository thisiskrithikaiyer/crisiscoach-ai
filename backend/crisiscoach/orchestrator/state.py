from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class CrisisCoachState(TypedDict):
    # Conversation
    messages: Annotated[list, add_messages]
    user_id: str

    # Routing
    intent: str         
    agent: str         
    intake_complete: bool  
    phase: str          

    # User snapshot (populated by context_builder)
    days_since: int | None
    days_left: int | None
    mood_score: int | None        # 1-10 from last check-in
    energy_score: int | None      # 1-10 from last check-in
    open_tasks: int | None        # uncompleted plan items
    tracking_summary: dict | None # last 10 days of checkins + task completion (goal_planner only)
    tracking_skills: dict | None  # current skill set
    talent_map: dict | None       # structured skills graph from background talent_mapper
    
    # Response
    response: str
    sources: list[str]            # citations from RAG
