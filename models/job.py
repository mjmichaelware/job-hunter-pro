from typing import Optional, List
from pydantic import BaseModel, Field

class Job(BaseModel):
    """
    Represents the canonical, deduplicated Job entity.
    This record is long-lived and updated over time.
    """
    canonical_key: str = Field(..., description="SHA-256 hash of (title + normalized place + address) for deduplication.")
    title: str
    company: str
    industry: str
    role_family: str
    role_tags: List[str] = Field(default_factory=list)
    latest_source_url: Optional[str] = None
    place_id: Optional[str] = Field(None, description="Google Places ID for the job location.")
    first_seen_at: str
    last_seen_at: str
    seen_count: int = 1
