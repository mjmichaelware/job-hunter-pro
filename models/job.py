from dataclasses import dataclass, field
from typing import Optional, List
from ._base import Model


@dataclass
class Job(Model):
    """
    Represents the canonical, deduplicated Job entity.
    This record is long-lived and updated over time.
    """
    canonical_key: str
    title: str
    company: str
    industry: str
    role_family: str
    first_seen_at: str
    last_seen_at: str
    role_tags: List[str] = field(default_factory=list)
    latest_source_url: Optional[str] = None
    place_id: Optional[str] = None
    seen_count: int = 1
