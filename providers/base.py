from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, NamedTuple

from models import SearchResult

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
