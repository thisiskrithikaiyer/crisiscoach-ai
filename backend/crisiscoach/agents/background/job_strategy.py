"""Job strategy agent — weekly market data refresh and pipeline recommendations."""
import json
from openai import OpenAI
from crisiscoach.config import GROQ_API_KEY, GROQ_MODEL

_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


async def refresh_strategy(user_id: str) -> dict:
    from crisiscoach.db.supabase import get_client
    from crisiscoach.db.vector_store import query_collection

    sb = get_client()
    profile = sb.table("users").select("talent_map, runway_weeks").eq("id", user_id).single().execute()
    data = profile.data or {}
    talent_map = data.get("talent_map", {})

    target_roles = talent_map.get("target_roles", [])
    if not target_roles:
        return {"skipped": True, "reason": "no_target_roles"}

    # Pull relevant market intel from vector store
    query = f"job market trends for {', '.join(target_roles[:3])}"
    market_chunks = query_collection("job_strategy", query, n_results=4)

    context = json.dumps({
        "talent_map": talent_map,
        "runway_weeks": data.get("runway_weeks"),
        "market_intel": market_chunks,
    }, default=str)

    system = (
        "You are a job strategy advisor. Given the user's profile and market intel, "
        "output a weekly strategy recommendation as JSON only: "
        '{"priority_roles": [...], "companies_to_target": [...], "outreach_goal": <int>, '
        '"strategic_insight": "...", "avoid": "..."}. '
        "Be specific and data-driven. No motivational filler."
    )
    resp = _client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=512,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": context},
        ],
    )
    strategy = json.loads(resp.choices[0].message.content)
    sb.table("job_strategies").upsert({
        "user_id": user_id,
        "strategy": strategy,
    }, on_conflict="user_id").execute()

    return strategy
