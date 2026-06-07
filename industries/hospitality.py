from .base import IndustryRoute

hospitality_route = IndustryRoute(
    key="hospitality",
    label="Hospitality & Hotels",
    queries=[
        "hotel front desk jobs Salt Lake City",
        "banquet server jobs Salt Lake City",
        "hotel housekeeping jobs Salt Lake City",
        "hotel steward jobs Salt Lake City",
    ],
    positive_terms={
        "hotel", "front desk", "banquet", "banquet server", "housekeeping", "bellhop", 
        "concierge", "guest services", "resort", "valet", "night audit",
        "hotel restaurant", "pool server"
    },
    negative_terms={"registered nurse", "software", "warehouse"},
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
    background_sensitive=True,
)
