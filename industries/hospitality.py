from .base import IndustryRoute

hospitality_route = IndustryRoute(
    key="hospitality",
    label="Hospitality & Hotels",
    description="Jobs in hotels, event spaces, and other hospitality-focused businesses.",
    search_queries=[
        "hotel front desk jobs Salt Lake City",
        "banquet server jobs Salt Lake City",
        "hotel housekeeping jobs Salt Lake City",
        "hotel steward jobs Salt Lake City",
    ],
    match_keywords={
        "hotel", "front desk", "banquet", "housekeeping", "bellhop", 
        "concierge", "guest services", "resort", "valet", "night audit",
        "hotel restaurant", "pool server"
    },
    negative_keywords={"registered nurse", "software", "warehouse"},
    role_families={
        "front desk": "front-of-house",
        "guest services": "front-of-house",
        "concierge": "front-of-house",
        "bellhop": "front-of-house",
        "valet": "front-of-house",
        "banquet server": "food-service",
        "housekeeping": "operations",
        "night audit": "management",
    },
    is_background_sensitive=True,
)
