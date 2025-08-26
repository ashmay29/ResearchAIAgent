import io
from typing import Optional
from PyPDF2 import PdfReader


def extract_text(pdf_path: str) -> str:
    """Extract text from a PDF using PyPDF2 with fallbacks.
    Returns a best-effort concatenation of page texts.
    """
    text_parts = []
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        for i, page in enumerate(reader.pages):
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            if txt.strip():
                text_parts.append(txt)
    return "\n\n".join(text_parts)
