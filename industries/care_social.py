from .base import IndustryRoute

care_social_route = IndustryRoute(
    key="care_social",
    label="Care & Social Services",
    description="Roles providing direct care, peer support, and social services.",
    search_queries=[
        "peer support specialist jobs Salt Lake City",
        "behavioral health technician jobs Salt Lake City",
        "case aide jobs Salt Lake City",
        "direct support professional jobs Salt Lake City",
    ],
    match_keywords={
        "peer support", "behavioral health technician", "bht", "case aide", "dsp",
        "direct support", "recovery coach", "residential support", "intake coordinator",
        "social services"
    },
    negative_keywords={"registered nurse", "culinary", "retail cashier"},
    role_families={
        "peer support": "peer-support",
        "bht": "technician",
        "case aide": "social-work-support",
    },
    required_credentials=["BHT/CPSS", "CPR", "UT Dept Health Clearance"],
    is_background_sensitive=True,
)
