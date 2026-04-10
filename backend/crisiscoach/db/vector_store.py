"""ChromaDB-backed vector store using Groq's nomic-embed-text (free tier)."""
from functools import lru_cache
from typing import Any
import chromadb
from chromadb.config import Settings
from openai import AsyncOpenAI
from crisiscoach.config import CHROMA_PERSIST_DIR, GROQ_API_KEY

_embed_client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


@lru_cache(maxsize=1)
def _get_chroma() -> chromadb.Client:
    return chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection(name: str) -> chromadb.Collection:
    return _get_chroma().get_or_create_collection(name)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    resp = await _embed_client.embeddings.create(
        model="nomic-embed-text-v1_5",
        input=texts,
    )
    return [item.embedding for item in resp.data]


def query_collection(name: str, query_text: str, n_results: int = 4) -> list[dict[str, Any]]:
    """Synchronous query — returns list of metadata dicts with 'document' and 'source' keys."""
    import asyncio
    embeddings = asyncio.run(embed_texts([query_text]))
    collection = get_collection(name)
    results = collection.query(query_embeddings=embeddings, n_results=n_results)
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    return [{"document": d, **m} for d, m in zip(docs, metas)]
