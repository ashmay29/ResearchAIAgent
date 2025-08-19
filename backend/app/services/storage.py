import os
import shutil
import uuid
from ..config import settings

class Storage:
    def save_upload(self, fileobj, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        paper_id = str(uuid.uuid4())
        out = os.path.join(settings.storage_dir, paper_id + ext)
        with open(out, "wb") as f:
            shutil.copyfileobj(fileobj, f)
        return paper_id, out

storage = Storage()
