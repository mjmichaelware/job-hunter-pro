from typing import Dict, List, Optional
from .base import IndustryRoute, score_text_for_industry
from .food_service import food_service_route
from .hospitality import hospitality_route
from .sales import sales_route
from .customer_service import customer_service_route
from .care_social import care_social_route
from .retail_ops import retail_ops_route

# The single source of truth for all defined industry routes.
_INDUSTRY_REGISTRY: Dict[str, IndustryRoute] = {
    route.key: route for route in [
        food_service_route,
        hospitality_route,
        sales_route,
        customer_service_route,
        care_social_route,
        retail_ops_route,
    ]
}

def get_all_routes() -> List[IndustryRoute]:
    """Returns a list of all registered industry routes."""
    return list(_INDUSTRY_REGISTRY.values())

def get_route(key: str) -> Optional[IndustryRoute]:
    """Looks up an industry route by its unique key."""
    return _INDUSTRY_REGISTRY.get(key)

def list_industries() -> List[str]:
    """Returns a list of all registered industry keys."""
    return list(_INDUSTRY_REGISTRY.keys())

def classify_text(text: str) -> Optional[str]:
    """
    Deterministically classifies text into one of the registered industries.
    Returns the key of the best matching industry route, or None if no positive match.
    Requires at least one positive term hit (score >= 1) to avoid assigning an
    industry just because it scored least-bad-of-zero.
    """
    best_key = None
    best_score = 0.0

    for key, route in _INDUSTRY_REGISTRY.items():
        score = score_text_for_industry(text, route)
        if score > best_score:
            best_score = score
            best_key = key

    # Minimum positive evidence required — a score of 0 means no terms matched.
    return best_key if best_score >= 1.0 else None

__all__ = [
    "get_all_routes",
    "get_route",
    "list_industries",
    "classify_text",
    "IndustryRoute",
    "food_service_route",
    "hospitality_route",
    "sales_route",
    "customer_service_route",
    "care_social_route",
    "retail_ops_route",
]
