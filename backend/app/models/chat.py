from pydantic import BaseModel
from typing import Literal


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    max_tokens: int = 1024


class ChatResponse(BaseModel):
    reply: str
    input_tokens: int
    output_tokens: int
