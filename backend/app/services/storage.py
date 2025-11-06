import os
import shutil
import uuid
import json
from typing import Dict, Tuple
from ..config import settings

class Storage:
    def __init__(self):
        self.index_path = os.path.join(settings.storage_dir, "papers_index.json")
        self._load_index()
    
    def _load_index(self) -> None:
        """Load papers index from disk on startup."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    self.papers = json.load(f)
            except Exception:
                self.papers = {}
        else:
            self.papers = {}
    
    def _save_index(self) -> None:
        """Persist papers index to disk."""
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self.papers, f, ensure_ascii=False, indent=2)
    
    def save_upload(self, fileobj, filename: str) -> Tuple[str, str]:
        ext = os.path.splitext(filename)[1].lower()
        paper_id = str(uuid.uuid4())
        out = os.path.join(settings.storage_dir, paper_id + ext)
        with open(out, "wb") as f:
            shutil.copyfileobj(fileobj, f)
        # Persist to index
        self.papers[paper_id] = {"path": out, "filename": filename}
        self._save_index()
        return paper_id, out
    
    def get_paper(self, paper_id: str) -> Dict[str, str] | None:
        """Retrieve paper metadata by ID."""
        return self.papers.get(paper_id)
    
    def list_papers(self) -> Dict[str, Dict[str, str]]:
        """List all papers."""
        return self.papers

storage = Storage()
