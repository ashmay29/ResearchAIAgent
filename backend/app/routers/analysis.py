from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..agents.graph import pipeline
from .papers import PAPERS

router = APIRouter()

JOBS: dict[str, dict] = {}

class AnalyzeIn(BaseModel):
    paper_id: str
    options: Optional[dict] = None

@router.post("/run")
def run_analysis(payload: AnalyzeIn):
    paper = PAPERS.get(payload.paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    result = pipeline.run(paper["path"], payload.options or {}, paper_id=payload.paper_id)
    job_id = payload.paper_id  # simple mapping
    JOBS[job_id] = {"status": "done", "result": result}
    return {"job_id": job_id}

@router.get("/status/{job_id}")
def status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return {"status": "pending", "progress": 0}
    return {"status": job["status"], "progress": 100, "result": job.get("result")}
