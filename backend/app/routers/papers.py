from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from ..services.storage import storage
from ..schemas.paper import UrlIn, PaperOptions
import requests
import os
import io
from ..services.ingest import ingest_pdf

router = APIRouter()

PAPERS: dict[str, dict] = {}

@router.post("/upload")
async def upload_pdf(background: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    paper_id, path = storage.save_upload(file.file, file.filename)
    PAPERS[paper_id] = {"path": path, "filename": file.filename}
    # Start ingestion asynchronously (extract text, embed chunks, upsert to Pinecone)
    background.add_task(ingest_pdf, paper_id, path, file.filename)
    return {"paper_id": paper_id, "filename": file.filename, "ingesting": True}

@router.post("/by-url")
async def paper_by_url(background: BackgroundTasks, payload: UrlIn):
    r = requests.get(str(payload.url), timeout=30)
    r.raise_for_status()
    filename = os.path.basename(str(payload.url).split("?")[0]) or "download.pdf"
    paper_id, path = storage.save_upload(io.BytesIO(r.content), filename)
    PAPERS[paper_id] = {"path": path, "filename": filename}
    background.add_task(ingest_pdf, paper_id, path, filename)
    return {"paper_id": paper_id, "filename": filename, "ingesting": True}
