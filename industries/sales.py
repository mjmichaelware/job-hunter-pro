from .base import IndustryRoute

sales_route = IndustryRoute(
    key="sales",
    label="Sales",
    description="Roles focused on sales and business development.",
    search_queries=[
        "sales associate jobs Salt Lake City",
        "account executive jobs Salt Lake City",
        "retail sales jobs Salt Lake City",
    ],
    match_keywords={
        "sales", "account executive", "business development", "sales representative",
        "bdr", "sdr", "sales consultant"
    },
    negative_keywords={"registered nurse", "cook", "server"},
    role_families={
        "sales associate": "retail",
        "account executive": "b2b",
        "business development": "b2b",
    },
)
