from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.storage import storage
from ..schemas.paper import UrlIn, PaperOptions
import requests
import os
import io

router = APIRouter()

PAPERS: dict[str, dict] = {}

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    paper_id, path = storage.save_upload(file.file, file.filename)
    PAPERS[paper_id] = {"path": path, "filename": file.filename}
    return {"paper_id": paper_id, "filename": file.filename}

@router.post("/by-url")
async def paper_by_url(payload: UrlIn):
    r = requests.get(str(payload.url), timeout=30)
    r.raise_for_status()
    filename = os.path.basename(str(payload.url).split("?")[0]) or "download.pdf"
    paper_id, path = storage.save_upload(io.BytesIO(r.content), filename)
    PAPERS[paper_id] = {"path": path, "filename": filename}
    return {"paper_id": paper_id, "filename": filename}
