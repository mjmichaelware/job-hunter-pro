from .base import IndustryRoute

retail_ops_route = IndustryRoute(
    key="retail_ops",
    label="Retail & Operations",
    description="Jobs in retail environments, including sales, stock, and cashier roles.",
    search_queries=[
        "retail sales associate jobs Salt Lake City",
        "cashier jobs Salt Lake City",
        "stocking associate jobs Salt Lake City",
    ],
    match_keywords={
        "retail", "cashier", "stocking", "merchandising", "sales associate",
        "store associate", "team member"
    },
    negative_keywords={"registered nurse", "server", "cook", "driver"},
    role_families={
        "cashier": "front-of-store",
        "sales associate": "front-of-store",
        "stocking": "operations",
    },
)
