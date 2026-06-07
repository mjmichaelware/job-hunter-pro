from dataclasses import dataclass, field
from typing import List, Dict, Set

@dataclass(frozen=True)
class IndustryRoute:
    """
    Defines the deterministic routing and classification logic for a single industry.
    This is a pure data object with no I/O.
    """
    key: str
    label: str
    description: str
    
    # For discovery
    search_queries: List[str] = field(default_factory=list)

    # For classification
    match_keywords: Set[str] = field(default_factory=set)
    negative_keywords: Set[str] = field(default_factory=set)
    role_families: Dict[str, str] = field(default_factory=dict) # e.g., {"server": "front-of-house"}

    # For resolution and enrichment (placeholders for later stages)
    resolution_strategy: str = "default"
    required_credentials: List[str] = field(default_factory=list)
    is_background_sensitive: bool = False
