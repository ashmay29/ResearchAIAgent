import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    arxiv_api_base: str = os.getenv("ARXIV_API_BASE", "http://export.arxiv.org/api/query")

    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    gemini_embedding_model: str = os.getenv("GEMINI_EMBED_MODEL", "text-embedding-004")
    gemini_max_retries: int = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
    gemini_retry_backoff: float = float(os.getenv("GEMINI_RETRY_BACKOFF", "1.0"))
    
    # OPTIMIZED: Increased chunk size from 6000 to 8000 to reduce embedding calls by ~25%
    gemini_gen_chunk_bytes: int = int(os.getenv("GEMINI_GEN_CHUNK_BYTES", "8000"))
    
    gemini_max_output_tokens: int = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "2048"))
    gemini_max_context_bytes: int = int(os.getenv("GEMINI_MAX_CONTEXT_BYTES", "5000"))
    
    # OPTIMIZED: Increased from 30000 to handle larger papers without extra extraction call
    gemini_max_total_bytes: int = int(os.getenv("GEMINI_MAX_TOTAL_BYTES", "50000"))
    
    # OPTIMIZED: Effectively disabled extraction (set very high threshold)
    # This removes the extra API call for most papers
    gemini_extract_threshold: int = int(os.getenv("GEMINI_EXTRACT_THRESHOLD", "999999"))
    
    gemini_emb_trunc_bytes: int = int(os.getenv("GEMINI_EMB_TRUNC_BYTES", "24000"))
    gemini_probe_on_startup: bool = os.getenv("GEMINI_PROBE_ON_STARTUP", "false").lower() in {"1", "true", "yes"}
    gemini_verify_dim: bool = os.getenv("GEMINI_VERIFY_DIM", "false").lower() in {"1", "true", "yes"}

    pinecone_api_key: str | None = os.getenv("PINECONE_API_KEY")
    pinecone_index: str = os.getenv("PINECONE_INDEX", "research-summaries")
    pinecone_cloud: str = os.getenv("PINECONE_CLOUD", "aws")
    pinecone_region: str = os.getenv("PINECONE_REGION", "us-east-1")
    
    # UPDATED: Default dimension for text-embedding-004 is 768
    pinecone_dim: int = int(os.getenv("PINECONE_DIM", "768"))
    
    storage_dir: str = os.getenv("STORAGE_DIR", "storage") 

settings = Settings()

os.makedirs(settings.storage_dir, exist_ok=True)
