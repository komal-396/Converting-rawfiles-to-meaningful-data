"""Lightweight memory store: persists intent + reports for agent context retrieval."""
import uuid
from typing import Any, Dict, List

import chromadb

from core.config import CHROMA_DIR

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_collection = _client.get_or_create_collection("medallion_memory")


def store_document(text: str, metadata: Dict[str, Any] | None = None, doc_id: str | None = None) -> str:
    """Persist a document (business intent, report summary, etc.) for later retrieval."""
    doc_id = doc_id or uuid.uuid4().hex
    _collection.add(documents=[text], metadatas=[metadata or {}], ids=[doc_id])
    return doc_id


def retrieve_context(query: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """Semantic search over previously stored documents (past intents/reports)."""
    if _collection.count() == 0:
        return []
    n_results = min(n_results, _collection.count())
    results = _collection.query(query_texts=[query], n_results=n_results)
    return [
        {"document": doc, "metadata": meta}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]
