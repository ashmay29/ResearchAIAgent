from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os

from .routers import auth, papers, analysis, history, settings as settings_router
from .utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Research Paper Analyzer/Summarizer API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"]) 
app.include_router(papers.router, prefix="/papers", tags=["papers"]) 
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"]) 
app.include_router(history.router, prefix="/history", tags=["history"]) 
app.include_router(settings_router.router, prefix="/settings", tags=["settings"]) 

@app.get("/")
def root():
    return {"status": "ok", "service": "Research Paper Analyzer/Summarizer API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
