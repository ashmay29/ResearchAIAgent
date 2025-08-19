from __future__ import annotations
from typing import List, Iterable
import hashlib
import time
import os

import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec

from ..config import settings


def _lazy_genai_configured() -> bool:
    api = settings.gemini_api_key
    if not api:
        return False
    genai.configure(api_key=api)
    return True


def _embedding_for(text: str) -> List[float]:
    if not _lazy_genai_configured():
        raise RuntimeError("GEMINI_API_KEY not configured")
    model = settings.gemini_embedding_model or "text-embedding-004"
    # google-genai expects model name prefixed with 'models/'
    model_name = model if model.startswith("models/") else f"models/{model}"
    resp = genai.embed_content(model=model_name, content=text)
    return resp["embedding"] if isinstance(resp, dict) else resp.embedding  # type: ignore


def _chunk(text: str, max_tokens: int = 800) -> List[str]:
    # naive splitter by paragraphs; fallback to fixed-size chunks
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current: List[str] = []
    tokens = 0
    for p in paras:
        ptoks = max(1, len(p.split()))
        if tokens + ptoks > max_tokens and current:
            chunks.append("\n\n".join(current))
            current, tokens = [p], ptoks
        else:
            current.append(p)
            tokens += ptoks
    if current:
        chunks.append("\n\n".join(current))
    # if text had no paras, do fixed chunks
    if not chunks:
        words = text.split()
        for i in range(0, len(words), max_tokens):
            chunks.append(" ".join(words[i : i + max_tokens]))
    return chunks


class PineconeVectorStore:
    def __init__(self):
        if not settings.pinecone_api_key:
            raise RuntimeError("PINECONE_API_KEY not configured")
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index
        existing = {idx.name for idx in self.pc.list_indexes()}
        if self.index_name not in existing:
            self.pc.create_index(
                name=self.index_name,
                dimension=3072,  # Gemini text-embedding-004 dimension
                metric="cosine",
                spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
            )
            # Wait until ready
            while not self.pc.describe_index(self.index_name).status["ready"]:  # type: ignore
                time.sleep(1)
        self.index = self.pc.Index(self.index_name)

    def add(self, texts: List[str], namespace: str | None = None, metadata: dict | None = None, base_id: str | None = None):
        vects = []
        md = metadata or {}
        for i, t in enumerate(texts):
            emb = _embedding_for(t)
            vid = base_id or hashlib.md5((t[:64] + str(i)).encode()).hexdigest()
            vects.append({"id": f"{vid}-{i}", "values": emb, "metadata": {"text": t, **md}})
        self.index.upsert(vectors=vects, namespace=namespace)

    def add_document(self, doc_id: str, text: str, extra_meta: dict | None = None):
        chunks = _chunk(text)
        self.add(chunks, namespace="docs", metadata={"doc_id": doc_id, **(extra_meta or {})}, base_id=doc_id)

    def query(self, q: str, k: int = 5, namespace: str | None = None, filter: dict | None = None) -> List[dict]:
        emb = _embedding_for(q)
        res = self.index.query(vector=emb, top_k=k, include_metadata=True, namespace=namespace or "docs", filter=filter)
        matches = getattr(res, "matches", []) or res.get("matches", [])  # type: ignore
        out: List[dict] = []
        for m in matches:
            meta = m.metadata if hasattr(m, "metadata") else m.get("metadata", {})  # type: ignore
            out.append({
                "text": meta.get("text", ""),
                "score": float(getattr(m, "score", meta.get("score", 0.0))),
                "metadata": meta,
            })
        return out


# Singleton store
store = PineconeVectorStore()
