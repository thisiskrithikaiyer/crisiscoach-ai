"""Ingest US visa grace period rules for H-1B, OPT, L-1, etc."""
import asyncio
from crisiscoach.agents.background.fact_checker import ingest_document

COLLECTION = "visa_db"

SEED_CHUNKS = [
    "H-1B holders have a 60-day grace period after layoff to find a new sponsor, change status, or depart.",
    "OPT holders: if laid off, you have 90 days of unemployment allowance. STEM OPT has the same 90-day rule.",
    "L-1 visa holders have no official grace period — consult an immigration attorney immediately upon layoff.",
    "Starting a company on H-1B is possible via self-sponsorship through an LLC, but requires attorney guidance.",
    "Cap-gap protection applies to H-1B applicants with pending petitions through September 30 of the cap year.",
]

DISCLAIMER = "Immigration rules change frequently. Always verify with a licensed immigration attorney."


async def ingest_seed_data():
    return await ingest_document(
        collection_name=COLLECTION,
        source_url="crisiscoach://seed/visa",
        chunks=SEED_CHUNKS,
        metadata={"domain": "visa", "disclaimer": DISCLAIMER},
    )


if __name__ == "__main__":
    asyncio.run(ingest_seed_data())
