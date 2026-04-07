"""Ingest job search strategy content into vector store."""
import asyncio
from crisiscoach.agents.background.fact_checker import ingest_document

COLLECTION = "job_strategy"

SEED_CHUNKS = [
    "70-80% of jobs are filled through networking, not job boards. Warm outreach outperforms cold applications by 5x.",
    "Target 5-10 companies at depth rather than spray-and-pray across 50 job postings.",
    "A focused job search with 3 applications per week beats 30 unfocused applications.",
    "LinkedIn Easy Apply has the lowest conversion rate. Direct recruiter outreach converts 3x better.",
    "During a layoff, reactivate dormant connections first — people who already know you are fastest to refer.",
]


async def ingest_seed_data():
    return await ingest_document(
        collection_name=COLLECTION,
        source_url="crisiscoach://seed/strategy",
        chunks=SEED_CHUNKS,
        metadata={"domain": "job_strategy"},
    )


if __name__ == "__main__":
    asyncio.run(ingest_seed_data())
