from typing import Optional
from typing import Optional
from pydantic import BaseModel, Field

class Review(BaseModel):
    """
    A single review for a Place.
    """
    place_id: str = Field(..., description="Foreign key to the Place entity.")
    provider: str = Field(..., description="Source of the review (e.g., 'google_places').")
    rating: Optional[float] = None
    text: Optional[str] = None
    author: Optional[str] = None
    relative_time: Optional[str] = None
    source_url: Optional[str] = None
    created_at: str
