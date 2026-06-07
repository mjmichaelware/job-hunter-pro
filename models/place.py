from typing import Optional, List, Tuple
from pydantic import BaseModel, Field

class Place(BaseModel):
    """
    Represents the canonical, deduplicated Place entity (a restaurant, hotel, etc.).
    This record is long-lived and updated over time.
    """
    place_id: str = Field(..., description="Google Places ID, the primary key.")
    name: str
    address: str
    lat: float
    lng: float
    types: List[str] = Field(default_factory=list)
    latest_rating: Optional[float] = None
    latest_review_count: Optional[int] = None
    business_status: Optional[str] = None # e.g., "OPERATIONAL"
    updated_at: str
