from .base import IndustryRoute

sales_route = IndustryRoute(
    key="sales",
    label="Sales",
    queries=[
        "sales associate jobs Salt Lake City",
        "account executive jobs Salt Lake City",
        "retail sales jobs Salt Lake City",
    ],
    positive_terms={
        "sales", "account executive", "business development", "sales representative",
        "bdr", "sdr", "sales consultant"
    },
    negative_terms={"registered nurse", "cook", "server"},
    role_families={
        "sales associate": "retail",
        "account executive": "b2b",
        "business development": "b2b",
    },
)
