from .base import IndustryRoute

customer_service_route = IndustryRoute(
    key="customer_service",
    label="Customer Service",
    description="Roles focused on customer support and client services.",
    search_queries=[
        "customer service representative jobs Salt Lake City",
        "call center agent jobs Salt Lake City",
        "client support jobs Salt Lake City",
    ],
    match_keywords={
        "customer service", "call center", "help desk", "client support",
        "inbound", "outbound", "ticketing", "support agent", "scheduling coordinator"
    },
    negative_keywords={"registered nurse", "driver", "warehouse"},
    role_families={
        "call center": "phone-support",
        "help desk": "technical-support",
        "customer service": "general-support",
    },
)
