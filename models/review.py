from dataclasses import dataclass
from typing import Optional
from ._base import Model


@dataclass
class Review(Model):
    """
    A single review for a Place.
    """
    place_id: str
    provider: str
    created_at: str
    rating: Optional[float] = None
    text: Optional[str] = None
    author: Optional[str] = None
    relative_time: Optional[str] = None
    source_url: Optional[str] = None
