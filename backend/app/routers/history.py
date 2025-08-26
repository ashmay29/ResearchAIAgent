from fastapi import APIRouter
from ..utils.session_store import list_sessions

router = APIRouter()

@router.get("/list")
def list_history():
    sessions = list_sessions()
    items = [{"id": s.get("session_id") or s.get("paper_id"), "status": s.get("status", "done")} for s in sessions]
    return {"items": items}
