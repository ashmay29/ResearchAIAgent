import os
from pydantic import BaseModel

class Settings(BaseModel):
    arxiv_api_base: str = os.getenv("ARXIV_API_BASE", "http://export.arxiv.org/api/query")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    pinecone_api_key: str | None = os.getenv("PINECONE_API_KEY")
    chroma_dir: str = os.getenv("CHROMA_DIR", ".chroma")
    storage_dir: str = os.getenv("STORAGE_DIR", "storage")

settings = Settings()

os.makedirs(settings.storage_dir, exist_ok=True)
