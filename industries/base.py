import re
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
    queries: List[str] = field(default_factory=list)
    positive_terms: Set[str] = field(default_factory=set)
    negative_terms: Set[str] = field(default_factory=set)
    role_families: Dict[str, str] = field(default_factory=dict) # e.g., {"server": "front-of-house"}
    credentials: List[str] = field(default_factory=list)
    background_sensitive: bool = False
    remote_allowed: bool = False
    resolution_strategy: str = "default"

def term_present(term: str, text: str) -> bool:
    """
    Checks if a term/phrase is present in text with exact token/phrase boundaries.
    Prevents substring matches like 'rn' in 'morning'.
    """
    if not term or not text:
        return False
    # Use word boundaries \b for exact token matching.
    # Note: \b doesn't work perfectly for phrases with spaces if not handled carefully,
    # but for simple keywords and phrases it's generally what we want.
    # We escape the term to handle any special regex characters.
    pattern = rf"\b{re.escape(term.lower())}\b"
    return bool(re.search(pattern, text.lower()))

def score_text_for_industry(text: str, route: IndustryRoute) -> float:
    """
    Calculates a deterministic score for how well text matches an industry route.
    Score = (positive_matches - negative_matches * 10).
    If any negative term is present, the score should ideally be very low/negative.
    """
    if not text:
        return 0.0
    
    pos_count = sum(1 for term in route.positive_terms if term_present(term, text))
    neg_count = sum(1 for term in route.negative_terms if term_present(term, text))
    
    # Negative terms are strong signals for rejection.
    return float(pos_count - (neg_count * 10.0))
