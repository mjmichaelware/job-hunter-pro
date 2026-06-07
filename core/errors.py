class JobHunterError(Exception):
    """Base exception class for the application."""
    pass

class ConfigurationError(JobHunterError):
    """Raised when a required configuration is missing."""
    pass

class ProviderError(JobHunterError):
    """Raised when an external data provider fails."""
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
