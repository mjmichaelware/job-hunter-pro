from typing import Dict, Any
from ingest.oidc import VerifiedClaims

class SchedulerJob:
    """Represents a scheduled job triggered by Cloud Scheduler."""
    def __init__(self, payload: Dict[str, Any], verified_claims: VerifiedClaims):
        self.payload = payload
        self.verified_claims = verified_claims

    @property
    def name(self) -> str:
        return self.payload.get("name", "unknown")

    @property
    def target(self) -> str:
        return self.payload.get("target", "unknown")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payload": self.payload,
            "verified_claims": self.verified_claims._claims,
        }
