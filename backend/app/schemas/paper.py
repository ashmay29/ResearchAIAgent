from pydantic import BaseModel, HttpUrl
from typing import Optional

class PaperOptions(BaseModel):
    summary_length: str = "medium"  # short|medium|long
    focus: Optional[str] = None  # e.g., methodology, results
    feedback_type: str = "critique"  # critique|notes

class UrlIn(BaseModel):
    url: HttpUrl
    options: PaperOptions | None = None
