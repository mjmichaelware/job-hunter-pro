from enum import Enum

class RoleFamily(str, Enum):
    FRONT_OF_HOUSE = "front-of-house"
    BACK_OF_HOUSE = "back-of-house"
    MANAGEMENT = "management"
    FOOD_SERVICE = "food-service" # Fallback

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TriggerType(str, Enum):
    MANUAL = "MANUAL"
    SCHEDULER_OIDC = "SCHEDULER_OIDC"
    CRDT_PEER_SYNC = "CRDT_PEER_SYNC"

class ApplicationStatus(str, Enum):
    PREDICTED = "PREDICTED"
    DISCOVERED = "DISCOVERED"
    APPLIED = "APPLIED"
    INTERVIEWING = "INTERVIEWING"
    OFFER = "OFFER"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

class RejectionReason(str, Enum):
    NOT_FOOD_SERVICE = "not_food_service"
    NO_EXACT_ADDRESS = "no_exact_restaurant_address_resolved"
    RADIUS_UNAVAILABLE = "radius_unavailable"
    OUTSIDE_RADIUS = "outside_radius"
    TRANSIT_UNAVAILABLE = "transit_unavailable"
    TRANSIT_TOO_LONG = "transit_too_long"
    DUPLICATE = "duplicate"
    PROVIDER_ERROR = "provider_error"
    BUDGET_GUARD = "budget_guard"
    MISSING_SOURCE_URL = "missing_source_url"
    AMBIGUOUS_RESOLUTION = "ambiguous_place_resolution"
    LOW_CONFIDENCE = "low_confidence_extraction"
