from typing import Optional


def extract_text_from_pdf(path: str) -> str:
    try:
        import PyPDF2  # type: ignore
    except Exception:
        # Fallback minimal parser
        with open(path, "rb") as f:
            return f.read().decode(errors="ignore") if hasattr(bytes, "decode") else ""

    text = []
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text.append(page_text)
    return "\n".join(text)
