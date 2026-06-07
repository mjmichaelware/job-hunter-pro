import os
from typing import Dict, Any, Optional

try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

class OIDCError(Exception):
    """Base exception for OIDC validation failures."""
    
class InvalidTokenError(OIDCError):
    """Raised when the OIDC token itself is invalid."""
    
class InvalidIssuerError(OIDCError):
    """Raised when the token issuer is invalid."""
    
class InvalidAudienceError(OIDCError):
    """Raised when the token audience is invalid."""
    
class MissingAuthError(OIDCError):
    """Raised when authentication headers are missing."""

class VerifiedClaims:
    """Represents the verified claims from an OIDC token."""
    def __init__(self, claims: Dict[str, Any]):
        self._claims = claims

    def get(self, key: str, default: Any = None) -> Any:
        return self._claims.get(key, default)

    @property
    def email(self) -> Optional[str]:
        return self.get("email")

    @property
    def sub(self) -> Optional[str]:
        return self.get("sub")

def verify_token(
    auth_header: Optional[str],
    expected_audience: Optional[str] = None,
    expected_email: Optional[str] = None,
    fake_claims: Optional[Dict[str, Any]] = None,
) -> VerifiedClaims:
    """
    Verifies an OIDC token from the Authorization header.
    Supports real Google OIDC if google-auth is available, otherwise fails closed
    unless fake_claims are provided for testing.
    """
    if not auth_header or not auth_header.startswith("Bearer "):
        raise MissingAuthError("Authorization header missing or malformed.")

    token = auth_header.split(" ")[1]

    if fake_claims:
        claims = fake_claims
    elif GOOGLE_AUTH_AVAILABLE:
        try:
            # Note: In a real Cloud Run environment, expected_audience should be the service URL
            # or the configured audience.
            idinfo = id_token.verify_oauth2_token(
                token, google_requests.Request(), expected_audience
            )
            claims = idinfo
        except Exception as e:
            raise InvalidTokenError(f"Token verification failed: {str(e)}")
    else:
        raise InvalidTokenError("google-auth not available and no fake claims provided.")

    if expected_audience and claims.get("aud") != expected_audience:
        raise InvalidAudienceError(f"Invalid audience: {claims.get('aud')}")

    if expected_email and claims.get("email") != expected_email:
        raise InvalidTokenError(f"Email mismatch: {claims.get('email')} != {expected_email}")

    return VerifiedClaims(claims)
