from __future__ import annotations
from typing import List, Optional
import google.generativeai as genai

from ..config import settings


def _model() -> "genai.GenerativeModel":
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")
    genai.configure(api_key=settings.gemini_api_key)
    name = settings.gemini_model or "gemini-1.5-pro"
    return genai.GenerativeModel(name)


class LLMClient:
    def summarize(self, text: str, style: str = "medium", context: Optional[str] = None) -> str:
        prompt = (
            "You are an expert research assistant. Write a clear, structured overview of the paper. "
            f"Target length: {style}. Use bullet points where helpful."
        )
        if context:
            prompt += "\nUse the following relevant excerpts as context:\n" + context
        resp = _model().generate_content([
            {"text": prompt},
            {"text": "\nPaper content:"},
            {"text": text[:200000]},
        ])
        return resp.text.strip() if hasattr(resp, "text") else str(resp)

    def critique(self, text: str, context: Optional[str] = None) -> str:
        prompt = (
            "Provide a balanced critique focusing on methodology, assumptions, limitations, and potential improvements."
        )
        if context:
            prompt += "\nUse the following relevant excerpts as context:\n" + context
        resp = _model().generate_content([
            {"text": prompt},
            {"text": "\nPaper content:"},
            {"text": text[:200000]},
        ])
        return resp.text.strip() if hasattr(resp, "text") else str(resp)

    def key_findings(self, text: str, context: Optional[str] = None) -> List[str]:
        prompt = (
            "List the 5 most important key findings as concise bullet points. Return plain text bullets separated by new lines."
        )
        if context:
            prompt += "\nUse the following relevant excerpts as context:\n" + context
        resp = _model().generate_content([
            {"text": prompt},
            {"text": "\nPaper content:"},
            {"text": text[:200000]},
        ])
        text_out = resp.text or ""
        lines = [l.strip("- •\t ") for l in text_out.splitlines() if l.strip()]
        return [l for l in lines if l]

    def citations(self, text: str) -> List[str]:
        prompt = (
            "Extract up to 5 important citations or references mentioned in the paper. "
            "Return each as a single-line citation (authors, year, title if present)."
        )
        resp = _model().generate_content([
            {"text": prompt},
            {"text": "\nPaper content:"},
            {"text": text[:200000]},
        ])
        lines = [l.strip("- •\t ") for l in (resp.text or "").splitlines() if l.strip()]
        return lines[:5]


llm_client = LLMClient()
