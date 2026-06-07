from .base import IndustryRoute

care_social_route = IndustryRoute(
    key="care_social",
    label="Care & Social Services",
    queries=[
        "peer support specialist jobs Salt Lake City",
        "behavioral health technician jobs Salt Lake City",
        "case aide jobs Salt Lake City",
        "direct support professional jobs Salt Lake City",
    ],
    positive_terms={
        "peer support", "behavioral health technician", "bht", "case aide", "dsp",
        "direct support", "recovery coach", "residential support", "intake coordinator",
        "social services"
    },
    negative_terms={"registered nurse", "culinary", "retail cashier"},
    role_families={
        "peer support": "peer-support",
        "bht": "technician",
        "case aide": "social-work-support",
    },
    credentials=["BHT/CPSS", "CPR", "UT Dept Health Clearance"],
    background_sensitive=True,
)
