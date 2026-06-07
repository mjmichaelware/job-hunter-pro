from .base import IndustryRoute

customer_service_route = IndustryRoute(
    key="customer_service",
    label="Customer Service",
    queries=[
        "customer service representative jobs Salt Lake City",
        "call center agent jobs Salt Lake City",
        "client support jobs Salt Lake City",
    ],
    positive_terms={
        "customer service", "call center", "help desk", "client support",
        "inbound", "outbound", "ticketing", "support agent", "scheduling coordinator"
    },
    negative_terms={"registered nurse", "driver", "warehouse"},
    role_families={
        "call center": "phone-support",
        "help desk": "technical-support",
        "customer service": "general-support",
    },
)
