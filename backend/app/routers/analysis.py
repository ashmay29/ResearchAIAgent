from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict
import time
from ..agents.graph import pipeline
from .papers import PAPERS
from ..schemas.analysis import AnalysisRequest, AnalysisOptions
from ..utils.session_store import save_session, get_session, list_sessions
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.post("/run")
def run_analysis(payload: AnalysisRequest):
    """
    OPTIMIZED: Support single or multiple papers.
    Returns results keyed by paper_id to avoid mixing.
    """
    logger.info(f"[ENDPOINT] POST /analysis/run received for paper_ids={payload.paper_ids}")

    # Validate all papers exist
    missing = [pid for pid in payload.paper_ids if pid not in PAPERS]
    if missing:
        logger.error(f"[ENDPOINT] Papers not found: {missing}")
        raise HTTPException(status_code=404, detail=f"Papers not found: {missing}")

    try:
        # Process each paper separately to avoid mixing results
        results_by_paper: Dict[str, dict] = {}
        
        for paper_id in payload.paper_ids:
            paper = PAPERS[paper_id]
            logger.info(f"[ENDPOINT] Starting pipeline execution for paper_id={paper_id}")
            
            # Run analysis for this specific paper
            result = pipeline.run(
                paper["path"], 
                payload.options or AnalysisOptions(), 
                paper_id=paper_id
            )
            
            # Store with paper_id as key
            results_by_paper[paper_id] = result
            logger.info(f"[ENDPOINT] Analysis successful for paper_id={paper_id}")

        # Generate a job_id for the batch
        job_id = f"batch_{int(time.time())}_{len(payload.paper_ids)}_papers"

        # Save session with all results
        options_dict = payload.options.model_dump() if payload.options else {}
        save_session(job_id, {
            "paper_ids": payload.paper_ids,  # Track which papers were analyzed
            "options": options_dict,
            "status": "done",
            "results": results_by_paper,  # Dict keyed by paper_id
            "paper_count": len(payload.paper_ids),
        })

        logger.info(f"[ENDPOINT] Batch analysis successful for {len(payload.paper_ids)} papers")
        return {
            "job_id": job_id,
            "paper_count": len(payload.paper_ids),
            "paper_ids": payload.paper_ids
        }

    except Exception as e:
        logger.error(f"[ENDPOINT] Analysis failed: {e}")
        raise

@router.get("/status/{job_id}")
def status(job_id: str):
    """Get status and results for a job (single or multi-paper)."""
    job = get_session(job_id)
    if not job:
        return {"status": "pending", "progress": 0}
    
    # Return with clear structure
    return {
        "status": job.get("status", "done"),
        "progress": 100,
        "results": job.get("results"),  # Dict keyed by paper_id
        "paper_count": job.get("paper_count", 1),
        "paper_ids": job.get("paper_ids", [])
    }


@router.get("/sessions")
def sessions():
    return {"sessions": list_sessions()}


@router.get("/history/list")
def history_list():
    sessions = list_sessions()
    items = []
    for s in sessions:
        # Handle both old single-paper and new multi-paper sessions
        paper_ids = s.get("paper_ids", [s.get("paper_id")] if s.get("paper_id") else [])
        items.append({
            "id": s.get("session_id") or s.get("paper_id"),
            "status": s.get("status", "done"),
            "paper_count": len(paper_ids),
            "paper_ids": paper_ids
        })
    return {"items": items}
