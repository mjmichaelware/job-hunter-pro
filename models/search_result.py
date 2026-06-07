from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, field_validator

class SearchResult(BaseModel):
    """
    A normalized result from any discovery provider.
    """
    provider: str = Field(..., description="The key of the provider that found this result.")
    query: str = Field(..., description="The search query that produced this result.")
    title: str = Field(..., description="The job title or page title.")
    url: str = Field(..., description="The canonical source URL.")
    snippet: Optional[str] = Field(None, description="A short description or snippet of the result.")
    source_name: Optional[str] = Field(None, description="The name of the source site (e.g., 'Glassdoor').")
    published_date: Optional[str] = Field(None, description="The publication date string, if available.")
    raw_json: Dict[str, Any] = Field(..., description="The original, unmodified JSON payload from the provider.")
    confidence: float = Field(1.0, description="Confidence score of the retrieval (0.0 to 1.0).")
    cost_units: float = Field(0.0, description="Estimated quota/cost units for this result.")

    @field_validator('url', mode='before')
    @classmethod
    def ensure_http_url(cls, v: Any) -> str:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith('www.'):
                return f'https://{v}'
        return str(v)
