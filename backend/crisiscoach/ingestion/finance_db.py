"""Ingest personal finance guidance for layoff survivors."""
import asyncio
from crisiscoach.agents.background.fact_checker import ingest_document

COLLECTION = "finance_db"

SEED_CHUNKS = [
    "Immediately cut discretionary spending to 50% on day one of layoff to extend runway without lifestyle shock.",
    "Roll your 401(k) to an IRA within 60 days of leaving; direct rollovers avoid the 20% withholding.",
    "File for unemployment insurance immediately — processing takes 2-4 weeks and back pay is not guaranteed.",
    "The 4% rule: if you need to estimate how long savings lasts, divide total savings by annual expenses × 25.",
    "HSA funds are yours to keep and can be used for COBRA premiums if you're unemployed.",
]


async def ingest_seed_data():
    return await ingest_document(
        collection_name=COLLECTION,
        source_url="crisiscoach://seed/finance",
        chunks=SEED_CHUNKS,
        metadata={"domain": "finance"},
    )


if __name__ == "__main__":
    asyncio.run(ingest_seed_data())
