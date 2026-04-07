"""Ingest company hiring signals and culture intel into vector store."""
import asyncio
from crisiscoach.agents.background.fact_checker import ingest_document

COLLECTION = "company_db"


async def ingest_company(
    company_name: str,
    hiring_signals: list[str],
    culture_notes: list[str],
    source_url: str,
):
    chunks = [
        f"{company_name} hiring signal: {s}" for s in hiring_signals
    ] + [
        f"{company_name} culture: {c}" for c in culture_notes
    ]
    return await ingest_document(
        collection_name=COLLECTION,
        source_url=source_url,
        chunks=chunks,
        metadata={"company": company_name, "domain": "company_intel"},
    )


async def ingest_seed_data():
    await ingest_company(
        company_name="Example Corp",
        hiring_signals=["Posted 12 SWE roles in last 30 days", "Recently raised Series B"],
        culture_notes=["Known for async culture", "Strong eng blog with technical depth"],
        source_url="crisiscoach://seed/company/example",
    )


if __name__ == "__main__":
    asyncio.run(ingest_seed_data())
