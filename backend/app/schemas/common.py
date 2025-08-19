from pydantic import BaseModel
from typing import Optional, List

class Message(BaseModel):
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int = 0
    detail: Optional[str] = None

class Citation(BaseModel):
    title: str
    authors: list[str]
    year: int | None = None
    link: str | None = None
