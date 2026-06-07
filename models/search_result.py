from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, HttpUrl, field_validator

class SearchResult(BaseModel):
    """
    A normalized result from any discovery provider.
    """
    provider: str = Field(..., description="Name of the source provider (e.g., 'serpapi_jobs')")
    query: str = Field(..., description="The original search query used.")
    title: str = Field(..., description="The job or result title.")
    url: HttpUrl = Field(..., description="The canonical URL to the job listing or result.")
    snippet: Optional[str] = Field(None, description="A short description or snippet of the result.")
    published_date: Optional[str] = Field(None, description="The publication date string, if available.")
    source_name: Optional[str] = Field(None, description="The name of the source site (e.g., 'Glassdoor').")
    raw_json: Dict[str, Any] = Field(..., description="The original, unmodified JSON payload from the provider.")
    confidence: float = Field(1.0, description="Confidence score of the retrieval (0.0 to 1.0).")
    cost_units: float = Field(0.0, description="Estimated cost units for this API call.")

    @field_validator('url', mode='before')
    @classmethod
    def ensure_http_url(cls, v: Any) -> str:
        if isinstance(v, str) and v.startswith('www.'):
            return f'https://{v}'
        return v
