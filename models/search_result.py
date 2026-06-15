from dataclasses import dataclass, field
from typing import Optional, Any, Dict
from ._base import Model


@dataclass
class SearchResult(Model):
    """
    A normalized result from any discovery provider.
    """
    provider: str
    query: str
    title: str
    url: str
    snippet: Optional[str] = None
    source_name: Optional[str] = None
    published_date: Optional[str] = None
    raw_json: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    cost_units: float = 0.0

    def __post_init__(self) -> None:
        # Normalize the URL the way the old pydantic validator did:
        # bare "www." hosts become https://, everything else is coerced to str.
        if isinstance(self.url, str):
            v = self.url.strip()
            if v.startswith("www."):
                v = f"https://{v}"
            self.url = v
        else:
            self.url = str(self.url)
