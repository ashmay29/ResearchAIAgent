import os
from pydantic import BaseModel

class Settings(BaseModel):
    arxiv_api_base: str = os.getenv("ARXIV_API_BASE", "http://export.arxiv.org/api/query")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    # Gemini
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    gemini_embedding_model: str = os.getenv("GEMINI_EMBED_MODEL", "text-embedding-004")
    # Pinecone
    pinecone_api_key: str | None = os.getenv("PINECONE_API_KEY")
    pinecone_index: str = os.getenv("PINECONE_INDEX", "research-summaries")
    pinecone_cloud: str = os.getenv("PINECONE_CLOUD", "aws")
    pinecone_region: str = os.getenv("PINECONE_REGION", "us-east-1")
    chroma_dir: str = os.getenv("CHROMA_DIR", ".chroma")
    storage_dir: str = os.getenv("STORAGE_DIR", "storage")

settings = Settings()

os.makedirs(settings.storage_dir, exist_ok=True)
