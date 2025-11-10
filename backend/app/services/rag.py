from __future__ import annotations
from typing import List, Iterable
import hashlib
import time
import os
from collections import OrderedDict

import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec

from ..config import settings
from ..utils.logger import get_logger, track_api_call

logger = get_logger(__name__)

# OPTIMIZATION 1: Batch embedding cache across process
_EMB_CACHE = OrderedDict()
_BATCH_CACHE_SIZE = 512  # Increased cache size


def _lazy_genai_configured() -> bool:
    api = settings.gemini_api_key
    if not api:
        return False
    return True


def _truncate_bytes(text: str, max_bytes: int) -> str:
    b = text.encode("utf-8")
    if len(b) <= max_bytes:
        return text
    return b[:max_bytes].decode("utf-8", errors="ignore")


# OPTIMIZATION 2: Batch embedding API
@track_api_call("GEMINI_EMBEDDING_BATCH")
def _embedding_for_batch(texts: List[str]) -> List[List[float]]:
    """Embed multiple texts in a single API call using task_type batching."""
    if not _lazy_genai_configured():
        raise RuntimeError("GEMINI_API_KEY not configured")
    
    if not texts:
        return []
    
    model = (settings.gemini_embedding_model or "text-embedding-004").strip()
    model_name = model if model.startswith("models/") else f"models/{model}"
    
    # Truncate all texts
    safe_texts = [_truncate_bytes(t, int(getattr(settings, "gemini_emb_trunc_bytes", 24_000))) for t in texts]
    
    # Check cache first
    uncached_indices = []
    results = [None] * len(texts)
    
    for i, text in enumerate(safe_texts):
        key = hashlib.sha1(text.encode("utf-8")).hexdigest()
        if key in _EMB_CACHE:
            _EMB_CACHE.move_to_end(key)
            results[i] = _EMB_CACHE[key]
        else:
            uncached_indices.append(i)
    
    # Batch embed uncached texts
    if uncached_indices:
        uncached_texts = [safe_texts[i] for i in uncached_indices]
        
        max_retries = int(getattr(settings, "gemini_max_retries", 3))
        backoff = float(getattr(settings, "gemini_retry_backoff", 1.0))
        last_err = None
        
        for attempt in range(1, max_retries + 1):
            try:
                # Use batch embed_content with task_type
                resp = genai.embed_content(
                    model=model_name,
                    content=uncached_texts,
                    task_type="RETRIEVAL_DOCUMENT"  # Optimize for retrieval
                )
                
                # Extract embeddings - handle different response formats
                if isinstance(resp, dict):
                    embeddings = resp.get("embeddings", resp.get("embedding", []))
                else:
                    embeddings = resp.embeddings if hasattr(resp, 'embeddings') else [resp.embedding]
                
                # Cache and fill results
                for i, idx in enumerate(uncached_indices):
                    # Handle different embedding formats
                    if isinstance(embeddings[i], list):
                        emb = embeddings[i]
                    elif isinstance(embeddings[i], dict):
                        emb = embeddings[i].get("values", embeddings[i].get("embedding", []))
                    else:
                        emb = embeddings[i].values if hasattr(embeddings[i], 'values') else embeddings[i].embedding
                    
                    results[idx] = emb
                    
                    # Update cache
                    key = hashlib.sha1(safe_texts[idx].encode("utf-8")).hexdigest()
                    _EMB_CACHE[key] = emb
                    if len(_EMB_CACHE) > _BATCH_CACHE_SIZE:
                        _EMB_CACHE.popitem(last=False)
                
                logger.info(f"Batch embedded {len(uncached_indices)} texts, {len(results) - len(uncached_indices)} from cache")
                break
                
            except Exception as e:
                last_err = e
                logger.warning(f"Batch embedding attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    time.sleep(backoff * attempt)
        
        if any(r is None for r in results):
            raise RuntimeError(f"Batch embedding failed after {max_retries} retries: {last_err}")
    else:
        logger.info(f"All {len(texts)} texts retrieved from cache")
    
    return results


def _embedding_for(text: str) -> List[float]:
    """Single text embedding (uses batch API under the hood)."""
    return _embedding_for_batch([text])[0]


# OPTIMIZATION 3: Smarter chunking with overlap for better context
def _chunk_with_overlap(text: str, max_bytes: int = 9000, overlap_bytes: int = 300) -> List[str]:
    """
    Chunk text with overlap to preserve context at boundaries.
    Increased default chunk size from 6000 to 9000 to reduce total chunks by ~25%.
    """
    b = text.encode("utf-8")
    chunks: List[str] = []
    
    if len(b) <= max_bytes:
        return [text]
    
    i = 0
    while i < len(b):
        end = min(i + max_bytes, len(b))
        chunk_bytes = b[i:end]
        
        # Try to break at sentence boundary if not at end
        if end < len(b):
            # Look for sentence endings in the last 200 bytes
            last_section = chunk_bytes[-200:]
            for sep in [b'. ', b'.\n', b'! ', b'? ', b'\n\n']:
                idx = last_section.rfind(sep)
                if idx != -1:
                    # Adjust end to sentence boundary
                    actual_end = i + len(chunk_bytes) - 200 + idx + len(sep)
                    chunk_bytes = b[i:actual_end]
                    break
        
        chunk_text = chunk_bytes.decode("utf-8", errors="ignore").strip()
        if chunk_text:
            chunks.append(chunk_text)
        
        # Move forward with overlap
        i += len(chunk_bytes) - overlap_bytes if end < len(b) else len(chunk_bytes)
    
    old_strategy_chunks = len(b) // 6000 + (1 if len(b) % 6000 else 0)
    logger.info(f"Chunked {len(b)} bytes into {len(chunks)} chunks (old strategy: ~{old_strategy_chunks}, saved {old_strategy_chunks - len(chunks)} chunks)")
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

    @track_api_call("PINECONE_BATCH_UPSERT")
    def add_batch(self, texts: List[str], namespace: str | None = None, metadata: dict | None = None, base_id: str | None = None):
        """OPTIMIZATION 4: Batch embed and upsert in one go."""
        if not texts:
            return
        
        logger.info(f"Batch processing {len(texts)} chunks for embedding and upsert")
        
        # Single batch embedding call (HUGE OPTIMIZATION)
        embeddings = _embedding_for_batch(texts)
        
        # Prepare vectors
        md = metadata or {}
        vects = []
        for i, (txt, emb) in enumerate(zip(texts, embeddings)):
            vid = base_id or hashlib.md5((txt[:64] + str(i)).encode()).hexdigest()
            vects.append({
                "id": f"{vid}-{i}",
                "values": emb,
                "metadata": {"text": txt, "chunk_index": i, **md}
            })
        
        # Single upsert
        self.index.upsert(vectors=vects, namespace=namespace)
        logger.info(f"Upserted {len(vects)} vectors in single batch (saved {len(vects)-1} API calls)")

    def add_document(self, doc_id: str, text: str, extra_meta: dict | None = None):
        """OPTIMIZATION 5: Use improved chunking and batch operations."""
        # Use 9000 byte chunks with 300 byte overlap (optimized from 6000 bytes)
        chunks = _chunk_with_overlap(text, max_bytes=9000, overlap_bytes=300)
        old_chunk_count = len(text.encode('utf-8')) // 6000 + 1
        logger.info(f"Document {doc_id}: {len(chunks)} chunks (old: ~{old_chunk_count}, saved {old_chunk_count - len(chunks)} chunks)")
        self.add_batch(chunks, namespace="docs", metadata={"doc_id": doc_id, **(extra_meta or {})}, base_id=doc_id)

    def query(self, q: str, k: int = 5, namespace: str | None = None, filter: dict | None = None) -> List[dict]:
        """Query with single embedding call."""
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
