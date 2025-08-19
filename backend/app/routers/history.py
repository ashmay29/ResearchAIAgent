from fastapi import APIRouter
from .analysis import JOBS

router = APIRouter()

@router.get("/list")
def list_history():
    items = []
    for job_id, job in JOBS.items():
        items.append({"id": job_id, "status": job["status"]})
    return {"items": items}
