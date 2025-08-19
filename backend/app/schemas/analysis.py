from pydantic import BaseModel
from typing import List, Optional
from .common import Citation

class AnalysisRequest(BaseModel):
    paper_id: str
    options: dict | None = None

class Section(BaseModel):
    title: str
    content: str

class AnalysisResult(BaseModel):
    paper_id: str
    summary_sections: List[Section]
    feedback: str
    key_findings: List[str]
    citations: List[Citation]
