from dataclasses import dataclass, field
from typing import Optional, List
from ._base import Model


@dataclass
class Place(Model):
    """
    Represents the canonical, deduplicated Place entity (a restaurant, hotel, etc.).
    This record is long-lived and updated over time.
    """
    place_id: str
    name: str
    address: str
    lat: float
    lng: float
    updated_at: str
    types: List[str] = field(default_factory=list)
    latest_rating: Optional[float] = None
    latest_review_count: Optional[int] = None
    business_status: Optional[str] = None  # e.g., "OPERATIONAL"
