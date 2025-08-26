from __future__ import annotations
from typing import List, Iterable
import hashlib
import time
import os
from collections import OrderedDict

import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


def _lazy_genai_configured() -> bool:
    api = settings.gemini_api_key
    if not api:
        return False
    genai.configure(api_key=api)
    return True


def _truncate_bytes(text: str, max_bytes: int) -> str:
    b = text.encode("utf-8")
    if len(b) <= max_bytes:
        return text
    return b[:max_bytes].decode("utf-8", errors="ignore")


def _embedding_for(text: str) -> List[float]:
    if not _lazy_genai_configured():
        raise RuntimeError("GEMINI_API_KEY not configured")
    model = (settings.gemini_embedding_model or "text-embedding-004").strip()
    model_name = model if model.startswith("models/") else f"models/{model}"
    safe_text = _truncate_bytes(text, int(getattr(settings, "gemini_emb_trunc_bytes", 24_000)))

    # In-process LRU cache to avoid duplicate calls for identical content
    global _EMB_CACHE
    if '_EMB_CACHE' not in globals():
        _EMB_CACHE = OrderedDict()  # type: ignore[var-annotated]
    cache_max = int(os.getenv("GEMINI_EMB_CACHE_SIZE", "256"))
    key = hashlib.sha1(safe_text.encode("utf-8")).hexdigest()
    if key in _EMB_CACHE:
        # move to end (recently used)
        _EMB_CACHE.move_to_end(key)
        return _EMB_CACHE[key]

    max_retries = int(getattr(settings, "gemini_max_retries", 3))
    backoff = float(getattr(settings, "gemini_retry_backoff", 1.0))
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = genai.embed_content(model=model_name, content=safe_text)
            emb = resp["embedding"] if isinstance(resp, dict) else resp.embedding  # type: ignore
            # store in LRU cache
            _EMB_CACHE[key] = emb
            if len(_EMB_CACHE) > cache_max:
                _EMB_CACHE.popitem(last=False)
            return emb
        except Exception as e:  # broad catch to log and retry
            last_err = e
            logger.warning(f"Embedding attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(backoff * attempt)
            else:
                break
    raise RuntimeError(f"Embedding failed after {max_retries} retries: {last_err}")


def _chunk(text: str, max_bytes: int = 6000) -> List[str]:
    # Byte-based chunking to satisfy embedding payload limits.
    b = text.encode("utf-8")
    chunks: List[str] = []
    for i in range(0, len(b), max_bytes):
        piece = b[i : i + max_bytes].decode("utf-8", errors="ignore")
        if piece.strip():
            chunks.append(piece)
    return chunks


class PineconeVectorStore:
    def __init__(self):
        if not settings.pinecone_api_key:
            raise RuntimeError("PINECONE_API_KEY not configured")
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index
        # Decide whether we need to probe Gemini for embedding dimension
        existing = {idx.name for idx in self.pc.list_indexes()}
        need_index = self.index_name not in existing
        env_dim_raw = os.getenv("PINECONE_DIM")
        have_env_dim = bool(env_dim_raw)

        detected_emb_dim: int | None = None
        if need_index and not have_env_dim and settings.gemini_probe_on_startup:
            try:
                probe = _embedding_for("__dimension_probe__")
                detected_emb_dim = len(probe)
            except Exception as e:
                logger.warning(f"Embedding dim probe skipped/fallback (startup): {e}")

        desired_dim = int(env_dim_raw) if have_env_dim else int(detected_emb_dim or getattr(settings, "pinecone_dim", 1536))

        if need_index:
            self.pc.create_index(
                name=self.index_name,
                dimension=desired_dim,
                metric="cosine",
                spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
            )
            # Wait until ready
            while not self.pc.describe_index(self.index_name).status["ready"]:  # type: ignore
                time.sleep(1)
        self.index = self.pc.Index(self.index_name)

        # Optionally verify at startup (can make a Gemini call). Disabled by default.
        if settings.gemini_verify_dim:
            try:
                emb_dim = len(_embedding_for("__dimension_probe__"))
                if emb_dim != int(desired_dim):
                    msg = (
                        f"Embedding dim ({emb_dim}) does not match Pinecone index dim ({desired_dim}). "
                        f"Set PINECONE_DIM to {emb_dim} or switch embedding model to match. Current EMB model: '{settings.gemini_embedding_model}'."
                    )
                    logger.error(msg)
                    raise RuntimeError(msg)
                else:
                    logger.info(f"Embedding dimension verified: {emb_dim}")
            except Exception as e:
                if not isinstance(e, RuntimeError):
                    logger.warning(f"Could not verify embedding dimension at startup: {e}")

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


class _LazyPineconeStore:
    def __init__(self):
        self._inst: PineconeVectorStore | None = None

    def _ensure(self) -> PineconeVectorStore:
        if self._inst is None:
            self._inst = PineconeVectorStore()
        return self._inst

    def __getattr__(self, name):
        return getattr(self._ensure(), name)


# Lazy singleton proxy; no initialization work until first use
store = _LazyPineconeStore()
