from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from crisiscoach.orchestrator import build_graph
from crisiscoach.api.routes.auth import get_current_user

router = APIRouter()
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    user_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    intent: str
    sources: list[str] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    graph = get_graph()
    lc_messages = [
        HumanMessage(content=m.content) if m.role == "user" else
        type("AIMessage", (), {"content": m.content, "type": "ai"})()
        for m in request.messages
    ]
    initial_state = {
        "messages": lc_messages,
        "user_id": user.get("sub", request.user_id or ""),
        "intent": "",
        "agent": "",
        "days_since_layoff": None,
        "visa_deadline_days": None,
        "runway_weeks": None,
        "mood_score": None,
        "energy_score": None,
        "open_tasks": None,
        "response": "",
        "sources": [],
    }
    try:
        result = await graph.ainvoke(initial_state)
        return ChatResponse(
            reply=result.get("response", ""),
            intent=result.get("intent", "chat"),
            sources=result.get("sources", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
