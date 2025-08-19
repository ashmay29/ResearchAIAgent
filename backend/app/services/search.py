import requests
from urllib.parse import urlencode
from ..config import settings


def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
    }
    url = f"{settings.arxiv_api_base}?{urlencode(params)}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    # Minimal parse; recommend using feedparser for robust parsing
    entries = []
    for line in r.text.splitlines():
        if "<title>" in line and "arXiv" not in line:
            title = line.replace("<title>", "").replace("</title>", "").strip()
            if title:
                entries.append({"title": title})
    return entries[:max_results]
