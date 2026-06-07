from typing import Dict, Any, Optional

class OIDCError(Exception):
    """Base exception for OIDC validation failures."""
    pass

class InvalidTokenError(OIDCError):
    """Raised when the OIDC token itself is invalid."""
    pass

class InvalidIssuerError(OIDCError):
    """Raised when the token issuer is invalid."""
    pass

class InvalidAudienceError(OIDCError):
    """Raised when the token audience is invalid."""
    pass

class MissingAuthError(OIDCError):
    """Raised when authentication headers are missing."""
    pass

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
    expected_issuer: str,
    expected_audience: str,
    fake_claims: Optional[Dict[str, Any]] = None, # For local proof only
) -> VerifiedClaims:
    """
    Simulates OIDC token verification.
    In a real scenario, this would involve cryptography and external calls.
    """
    if not auth_header or not auth_header.startswith("Bearer "):
        raise MissingAuthError("Authorization header missing or malformed.")

    # In a real system, the token would be parsed and verified cryptographically.
    # For this proof, we use fake_claims.
    if fake_claims:
        claims = fake_claims
    else:
        # Simulate token parsing failure if no fake claims are provided for a real token
        raise InvalidTokenError("No real token verification implemented in proof mode.")

    if claims.get("iss") != expected_issuer:
        raise InvalidIssuerError(f"Invalid issuer: {claims.get('iss')}")

    if claims.get("aud") != expected_audience:
        raise InvalidAudienceError(f"Invalid audience: {claims.get('aud')}")

    return VerifiedClaims(claims)
