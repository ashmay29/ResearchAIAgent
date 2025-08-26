from __future__ import annotations
from typing import List, Optional
import time
import google.generativeai as genai

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


def _model() -> "genai.GenerativeModel":
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")
    genai.configure(api_key=settings.gemini_api_key)
    name = settings.gemini_model or "gemini-1.5-pro"
    return genai.GenerativeModel(name)


def _chunk_bytes(s: str, max_bytes: int) -> List[str]:
    b = s.encode("utf-8")
    out: List[str] = []
    for i in range(0, len(b), max_bytes):
        out.append(b[i : i + max_bytes].decode("utf-8", errors="ignore"))
    return [x for x in out if x.strip()]


def _gen_with_retry(parts: List[dict]) -> str:
    max_retries = int(getattr(settings, "gemini_max_retries", 3))
    backoff = float(getattr(settings, "gemini_retry_backoff", 1.0))
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = _model().generate_content(parts)
            return (resp.text or "").strip()
        except Exception as e:
            last_err = e
            logger.warning(f"Generation attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(backoff * attempt)
    raise RuntimeError(f"Generation failed after {max_retries} retries: {last_err}")


class LLMClient:
    def summarize(self, text: str, style: str = "medium", context: Optional[str] = None) -> str:
        prompt = (
            "You are an expert research assistant. Write a clear, structured overview of the paper. "
            f"Target length: {style}. Use bullet points where helpful."
        )
        if context:
            prompt += "\nUse the following relevant excerpts as context:\n" + context

        chunk_bytes = int(getattr(settings, "gemini_gen_chunk_bytes", 15000))
        parts = []
        outputs: List[str] = []
        for i, chunk in enumerate(_chunk_bytes(text, chunk_bytes)):
            parts = [{"text": prompt}, {"text": f"\nPaper content chunk {i+1}:",}, {"text": chunk}]
            outputs.append(_gen_with_retry(parts))
        return "\n\n".join([o for o in outputs if o])

    def critique(self, text: str, context: Optional[str] = None) -> str:
        prompt = (
            "Provide a balanced critique focusing on methodology, assumptions, limitations, and potential improvements."
        )
        if context:
            prompt += "\nUse the following relevant excerpts as context:\n" + context
        chunk_bytes = int(getattr(settings, "gemini_gen_chunk_bytes", 15000))
        outputs: List[str] = []
        for i, chunk in enumerate(_chunk_bytes(text, chunk_bytes)):
            parts = [{"text": prompt}, {"text": f"\nPaper content chunk {i+1}:"}, {"text": chunk}]
            outputs.append(_gen_with_retry(parts))
        return "\n\n".join([o for o in outputs if o])

    def key_findings(self, text: str, context: Optional[str] = None) -> List[str]:
        prompt = (
            "List the 5 most important key findings as concise bullet points. Return plain text bullets separated by new lines."
        )
        if context:
            prompt += "\nUse the following relevant excerpts as context:\n" + context
        chunk_bytes = int(getattr(settings, "gemini_gen_chunk_bytes", 15000))
        lines: List[str] = []
        for i, chunk in enumerate(_chunk_bytes(text, chunk_bytes)):
            parts = [{"text": prompt}, {"text": f"\nPaper content chunk {i+1}:"}, {"text": chunk}]
            text_out = _gen_with_retry(parts)
            lines.extend([l.strip("- •\t ") for l in text_out.splitlines() if l.strip()])
        # dedupe while preserving order
        seen = set()
        uniq = []
        for l in lines:
            if l not in seen:
                seen.add(l)
                uniq.append(l)
        return uniq[:5]

    def citations(self, text: str) -> List[str]:
        prompt = (
            "Extract up to 5 important citations or references mentioned in the paper. "
            "Return each as a single-line citation (authors, year, title if present)."
        )
        chunk_bytes = int(getattr(settings, "gemini_gen_chunk_bytes", 15000))
        lines: List[str] = []
        for i, chunk in enumerate(_chunk_bytes(text, chunk_bytes)):
            parts = [{"text": prompt}, {"text": f"\nPaper content chunk {i+1}:"}, {"text": chunk}]
            text_out = _gen_with_retry(parts)
            lines.extend([l.strip("- •\t ") for l in text_out.splitlines() if l.strip()])
        # lightly trim to 5
        return lines[:5]


llm_client = LLMClient()
