from dataclasses import dataclass
from typing import Optional, Any, Dict

@dataclass
class SearchResult:
    provider: str
    query: str
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None
    source_name: Optional[str] = None
    raw_json: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    cost_units: Optional[float] = None
