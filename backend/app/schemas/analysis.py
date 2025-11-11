from pydantic import BaseModel, Field
from pydantic import model_validator
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

# UPDATED: Support multiple papers with backward compatibility for single paper_id
class AnalysisRequest(BaseModel):
    paper_ids: Optional[List[str]] = Field(
        default=None,
        description="List of paper IDs to analyze (supports batch analysis)"
    )
    paper_id: Optional[str] = Field(
        default=None,
        description="Single paper ID (backward compatible)"
    )
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)

    @model_validator(mode="after")
    def _normalize_ids(self):
        # If only paper_id is provided, convert to paper_ids
        if (not self.paper_ids or len(self.paper_ids) == 0) and self.paper_id:
            self.paper_ids = [self.paper_id]
        # Validate presence
        if not self.paper_ids or len(self.paper_ids) == 0:
            raise ValueError("Either paper_ids (list) or paper_id (string) must be provided")
        return self

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
