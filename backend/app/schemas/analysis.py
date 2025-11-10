from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List, Dict
from .common import Citation

class OutputFormat(str, Enum):
    PARAGRAPHS = "paragraphs"
    BULLET_POINTS = "bullet_points"
    MIND_MAP = "mind_map"

class FocusArea(str, Enum):
    METHODOLOGY = "methodology"
    LITERATURE_REVIEW = "literature_review"
    RESULTS = "results"
    TECH_STACK = "technological_stack"
    OVERALL = "overall_context"

class AnalysisType(str, Enum):
    SUMMARY = "simple_summary"
    CRITIQUE = "critical_analysis"
    NOTES = "research_notes"

class AnalysisOptions(BaseModel):
    output_format: OutputFormat = Field(default=OutputFormat.PARAGRAPHS)
    focus_area: FocusArea = Field(default=FocusArea.OVERALL)
    analysis_type: AnalysisType = Field(default=AnalysisType.SUMMARY)

# UPDATED: Support multiple papers
class AnalysisRequest(BaseModel):
    paper_ids: List[str] = Field(
        description="List of paper IDs to analyze (supports batch analysis)"
    )
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)

class Section(BaseModel):
    title: str
    content: str

# UPDATED: Include paper identification
class AnalysisResult(BaseModel):
    paper_id: str
    paper_path: Optional[str] = None
    summary_sections: List[Section]
    feedback: str
    key_findings: List[str]
    citations: List[Citation]

# NEW: Batch analysis response
class BatchAnalysisResult(BaseModel):
    job_id: str
    paper_count: int
    paper_ids: List[str]
    results: Dict[str, AnalysisResult]
