import os
from openai import OpenAI
from app.models.chat import Message

SYSTEM_PROMPT = """You are CrisisCoach AI, a compassionate and trained crisis support companion.
Your role is to:
- Provide empathetic, non-judgmental support to people in distress
- Use evidence-based active listening techniques
- Guide users toward professional resources when appropriate
- Never provide medical diagnoses or replace professional mental health care
- Always prioritize user safety; if someone is in immediate danger, direct them to emergency services

Speak calmly, warmly, and clearly. If someone is in crisis, acknowledge their feelings before offering guidance."""

client = OpenAI(
    api_key=os.environ["GROK_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)


def chat(messages: list[Message], max_tokens: int = 1024) -> dict:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *[{"role": m.role, "content": m.content} for m in messages],
        ],
    )
    return {
        "reply": response.choices[0].message.content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
    }
