class JobHunterError(Exception):
    """Base exception class for the application."""
    pass

class ConfigurationError(JobHunterError):
    """Raised when a required configuration is missing."""
    pass

class ProviderError(JobHunterError):
    """Raised when an external data provider fails."""
    pass

class ProviderHardFailure(ProviderError):
    """Raised on a hard auth/rate-limit failure (401/403/429).

    The federated bridge catches this to quarantine the provider for the rest of
    the run instead of retrying it across every keyword.
    """
    def __init__(self, provider_key: str, status_code: int, message: str = ""):
        self.provider_key = provider_key
        self.status_code = status_code
        super().__init__(message or f"{provider_key} hard failure: HTTP {status_code}")

class GeocodingError(ProviderError):
    """Raised for errors related to the Geocoding API."""
    pass

class PlacesError(ProviderError):
    """Raised for errors related to the Places API."""
    pass

class DistanceMatrixError(ProviderError):
    """Raised for errors related to the Distance Matrix API."""
    pass

class BudgetGuardError(ProviderError):
    """Raised when an action is blocked by a budget/quota guard."""
    pass

class ResolutionError(JobHunterError):
    """Raised when a place or address cannot be resolved."""
    pass

class NormalizationError(JobHunterError):
    """Raised during the data normalization step."""
    pass

class PersistenceError(JobHunterError):
    """Raised for errors related to data storage."""
    pass
