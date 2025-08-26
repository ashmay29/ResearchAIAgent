import os
from ..config import settings
from .pdf import extract_text
from .rag import store
from ..utils.logger import get_logger

logger = get_logger(__name__)


def _text_path(paper_id: str) -> str:
    return os.path.join(settings.storage_dir, f"{paper_id}.txt")


def _marker_path(paper_id: str) -> str:
    return os.path.join(settings.storage_dir, f"{paper_id}.indexed")


def is_indexed(paper_id: str) -> bool:
    return os.path.exists(_marker_path(paper_id))


def ingest_pdf(paper_id: str, pdf_path: str, filename: str | None = None) -> None:
    """Extract text from PDF, persist plaintext for reuse, and index chunks in Pinecone.
    Creates a marker file to avoid duplicate indexing on subsequent runs.
    """
    try:
        if is_indexed(paper_id):
            logger.info(f"Ingest skipped; already indexed: {paper_id}")
            return
        text = extract_text(pdf_path)
        # Save plaintext for later reuse (analysis, QA, etc.)
        os.makedirs(settings.storage_dir, exist_ok=True)
        with open(_text_path(paper_id), "w", encoding="utf-8") as f:
            f.write(text)
        # Index chunks into Pinecone
        store.add_document(doc_id=paper_id, text=text, extra_meta={
            "doc_id": paper_id,
            "source_path": pdf_path,
            "filename": filename or os.path.basename(pdf_path),
        })
        # Write marker
        with open(_marker_path(paper_id), "w") as f:
            f.write("ok")
        logger.info(f"Ingest completed: {paper_id}")
    except Exception as e:
        logger.error(f"Ingest failed for {paper_id}: {e}")
        raise


def get_text(paper_id: str) -> str:
    """Return stored plaintext for the given paper_id if available, else empty string."""
    p = _text_path(paper_id)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    return ""
