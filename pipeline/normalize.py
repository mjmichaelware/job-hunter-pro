from typing import Dict, Any, Union
from models import SearchResult

def normalize_job(raw: Union[dict, SearchResult], provider: str = "test") -> dict:
    """
    Normalizes raw provider data or SearchResult object into a consistent Job dictionary.
    """
    if isinstance(raw, SearchResult):
        return {
            "title": raw.title,
            "company": raw.source_name or "Unknown",
            "description": raw.snippet or "",
            "url": str(raw.url),
            "provider": raw.provider,
            "query": raw.query,
            "raw_json": raw.raw_json,
            "confidence": raw.confidence,
        }
    
    # Fallback for raw dicts
    return {
        "title": raw.get("title", ""),
        "company": raw.get("company", raw.get("company_name", "Unknown")),
        "description": raw.get("description", raw.get("snippet", "")),
        "location": raw.get("location", ""),
        "url": raw.get("url", "https://example.com"),
        "provider": provider,
        "raw_json": raw,
    }
