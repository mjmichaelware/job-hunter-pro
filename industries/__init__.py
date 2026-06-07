from typing import Dict, List, Optional
from .base import IndustryRoute
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

def get_all_industries() -> List[IndustryRoute]:
    """Returns a list of all registered industry routes."""
    return list(_INDUSTRY_REGISTRY.values())

def get_industry_by_key(key: str) -> Optional[IndustryRoute]:
    """Looks up an industry route by its unique key."""
    return _INDUSTRY_REGISTRY.get(key)

__all__ = ["get_all_industries", "get_industry_by_key", "IndustryRoute"]
