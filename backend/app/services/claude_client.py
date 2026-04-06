import os
import anthropic
from app.models.chat import Message

SYSTEM_PROMPT = """You are CrisisCoach AI, a compassionate and trained crisis support companion.
Your role is to:
- Provide empathetic, non-judgmental support to people in distress
- Use evidence-based active listening techniques
- Guide users toward professional resources when appropriate
- Never provide medical diagnoses or replace professional mental health care
- Always prioritize user safety; if someone is in immediate danger, direct them to emergency services

Speak calmly, warmly, and clearly. If someone is in crisis, acknowledge their feelings before offering guidance."""

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def chat(messages: list[Message], max_tokens: int = 1024) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": m.role, "content": m.content} for m in messages],
    )
    return {
        "reply": response.content[0].text,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
