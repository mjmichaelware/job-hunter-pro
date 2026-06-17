from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, NamedTuple

from models import SearchResult


def check_hard_failure(provider_key: str, response) -> None:
    """Raise ProviderHardFailure on an auth/rate-limit status (401/403/429).

    Search adapters should call this immediately after an HTTP response so the
    federated bridge can quarantine a dead provider for the rest of the run
    instead of swallowing the error and re-hitting it on every keyword.
    """
    from services.provider_status import is_hard_failure
    from core.errors import ProviderHardFailure

    status = getattr(response, "status_code", None)
    if status is not None and is_hard_failure(status):
        raise ProviderHardFailure(provider_key, status)


class ProviderType(str, Enum):
    """Enum to differentiate types of providers."""
    SEARCH = "search"
    REASONING = "reasoning"

@dataclass(frozen=True)
class ProviderMetadata:
    """A standard data structure for provider metadata."""
    key: str
    label: str
    type: ProviderType
    description: str
    requires_api_key: bool = True
    # Budget class drives the budget guard generically (no central name list).
    # "free" = always affordable; "serpapi_quota" = gated on SerpAPI account quota.
    # A new provider declares its own cost behavior here.
    budget_class: str = "free"

class Provider(ABC):
    """Abstract Base Class for all providers."""
    
    @property
    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """All providers must expose their metadata."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the provider is configured and ready to use."""
        pass

    def disabled_reason(self) -> str:
        """Why this provider is intentionally turned off (empty string = enabled).

        Each provider owns its own on/off policy here so the registry, the
        federated bridge, and the API surface stay generic — no central list of
        provider names anywhere. Override to return a human-readable reason when
        a provider should be skipped (e.g. a broken/untrusted upstream that is
        off until an env flag re-enables it).
        """
        return ""

class SearchProvider(Provider):
    """Abstract Base Class for providers that discover jobs."""
    
    @abstractmethod
    def search(self, query: str) -> List[SearchResult]:
        """Performs a search and returns a list of normalized SearchResult objects."""
        pass

class ReasoningProvider(Provider):
    """Abstract Base Class for providers that enrich or classify data."""

    @abstractmethod
    def classify(self, text_content: str, categories: List[str]) -> Dict[str, Any]:
        """Classifies content into one of the given categories."""
        pass

    @abstractmethod
    def enrich(self, text_content: str) -> Dict[str, Any]:
        """Enriches content by extracting entities or summarizing."""
        pass
