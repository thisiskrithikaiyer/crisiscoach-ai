"""Talent mapper — builds a structured skills graph when user updates their profile."""
import json
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


async def map_talent(user_id: str, resume_text: str, linkedin_summary: str = "") -> dict:
    """
    Combine resume + LinkedIn to produce a structured skills + role-fit map.
    Persists to users.talent_map (JSONB column).
    """
    combined = f"Resume:\n{resume_text[:3000]}\n\nLinkedIn summary:\n{linkedin_summary[:1000]}"
    system = (
        "Analyze this professional background and output JSON only: "
        '{"top_skills": [...], "years_experience": <int>, "target_roles": [...], '
        '"industries": [...], "seniority": "junior|mid|senior|staff|principal", '
        '"adjacent_roles": [...], "transferable_strengths": [...]}. '
        "Be specific. No generic filler."
    )
    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=512,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": combined},
        ],
    )
    talent_map = json.loads(resp.choices[0].message.content)

    from crisiscoach.db.supabase import get_client
    sb = get_client()
    sb.table("users").update({"talent_map": talent_map}).eq("id", user_id).execute()

    return talent_map
