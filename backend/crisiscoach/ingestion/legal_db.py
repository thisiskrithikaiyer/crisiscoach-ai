"""Ingest employment law basics (US) for severance and rights questions."""
import asyncio
from crisiscoach.agents.background.fact_checker import ingest_document

COLLECTION = "legal_db"

SEED_CHUNKS = [
    "WARN Act requires 60-day notice for layoffs affecting 50+ employees at companies with 100+ workers. Violations mean back pay.",
    "Severance agreements often include a release of claims — you typically have 21 days to review and 7 days to revoke.",
    "Non-compete clauses are unenforceable in California, North Dakota, Oklahoma, and Minnesota (as of 2023).",
    "COBRA allows continuation of employer health insurance for 18 months post-layoff; you must elect within 60 days.",
    "Unemployment insurance eligibility: you must be laid off through no fault of your own. Apply within the first week.",
]

DISCLAIMER = "This content is for informational purposes only and is not legal advice. Consult an employment attorney for your situation."


async def ingest_seed_data():
    return await ingest_document(
        collection_name=COLLECTION,
        source_url="crisiscoach://seed/legal",
        chunks=SEED_CHUNKS,
        metadata={"domain": "legal", "disclaimer": DISCLAIMER},
    )


if __name__ == "__main__":
    asyncio.run(ingest_seed_data())
