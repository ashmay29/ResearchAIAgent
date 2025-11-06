from fastapi import APIRouter, HTTPException
from typing import Optional
import time
from ..agents.graph import pipeline
from .papers import PAPERS
from ..schemas.analysis import AnalysisRequest, AnalysisOptions
from ..utils.session_store import save_session, get_session, list_sessions

router = APIRouter()

@router.post("/run")
def run_analysis(payload: AnalysisRequest):
    from ..utils.logger import get_logger
    logger = get_logger(__name__)
    
    logger.info(f"[ENDPOINT] POST /analysis/run received for paper_id={payload.paper_id}")
    
    paper = PAPERS.get(payload.paper_id)
    if not paper:
        logger.error(f"[ENDPOINT] Paper not found: {payload.paper_id}")
        raise HTTPException(status_code=404, detail="Paper not found")
    
    try:
        # Run synchronously for now
        logger.info(f"[ENDPOINT] Starting pipeline execution for paper_id={payload.paper_id}")
        result = pipeline.run(paper["path"], payload.options or AnalysisOptions(), paper_id=payload.paper_id)
        
        # Persist session (compat: use paper_id as session id)
        job_id = payload.paper_id
        # Use Pydantic v2 model_dump() instead of dict()
        options_dict = payload.options.model_dump() if payload.options else {}
        save_session(job_id, {
            "paper_id": payload.paper_id,
            "options": options_dict,
            "status": "done",
            "result": result,
        })
        
        logger.info(f"[ENDPOINT] Analysis successful for paper_id={payload.paper_id}")
        return {"job_id": job_id}
        
    except Exception as e:
        logger.error(f"[ENDPOINT] Analysis failed for paper_id={payload.paper_id}: {e}")
        raise

@router.get("/status/{job_id}")
def status(job_id: str):
    job = get_session(job_id)
    if not job:
        return {"status": "pending", "progress": 0}
    return {"status": job.get("status", "done"), "progress": 100, "result": job.get("result")}

@router.get("/sessions")
def sessions():
    return {"sessions": list_sessions()}

@router.get("/history/list")
def history_list():
    sessions = list_sessions()
    items = [{"id": s.get("session_id") or s.get("paper_id"), "status": s.get("status", "done")} for s in sessions]
    return {"items": items}
