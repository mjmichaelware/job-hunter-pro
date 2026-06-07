from .base import IndustryRoute

retail_ops_route = IndustryRoute(
    key="retail_ops",
    label="Retail & Operations",
    queries=[
        "retail sales associate jobs Salt Lake City",
        "cashier jobs Salt Lake City",
        "stocking associate jobs Salt Lake City",
    ],
    positive_terms={
        "retail", "cashier", "stocking", "merchandising", "sales associate",
        "store associate", "team member", "inventory"
    },
    negative_terms={"registered nurse", "server", "cook", "driver"},
    role_families={
        "cashier": "front-of-store",
        "sales associate": "front-of-store",
        "stocking": "operations",
    },
)

