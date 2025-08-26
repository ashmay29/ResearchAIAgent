from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, List

from ..config import settings

SESS_DIR = os.path.join(settings.storage_dir, "sessions")
os.makedirs(SESS_DIR, exist_ok=True)


def _path(session_id: str) -> str:
    return os.path.join(SESS_DIR, f"{session_id}.json")


def save_session(session_id: str, data: Dict[str, Any]) -> None:
    data = {**data, "updated_at": int(time.time())}
    with open(_path(session_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_session(session_id: str) -> Dict[str, Any] | None:
    p = _path(session_id)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def list_sessions() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(SESS_DIR)):
        if not name.endswith(".json"):
            continue
        sid = name[:-5]
        data = get_session(sid)
        if data:
            items.append({"session_id": sid, **data})
    # most recent first
    items.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
    return items
