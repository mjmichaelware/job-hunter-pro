from typing import Dict, List, Optional, Tuple
from collections import Counter

from .base import Provider, ProviderType, SearchProvider, ReasoningProvider
from .search.serpapi_jobs import serpapi_jobs_provider
from .search.serpapi_organic import serpapi_organic_provider
from .search.adzuna import adzuna_provider
from .search.usajobs import usajobs_provider
from .search.jooble import jooble_provider
from .search.careerjet import careerjet_provider
from .search.themuse import themuse_provider
from .reasoning.openai import openai_provider
from .reasoning.gemini import gemini_provider
from .reasoning.claude import claude_provider
from .reasoning.groq import groq_provider
from .reasoning.xai import xai_provider

# The single source of truth for all defined providers.
_PROVIDER_REGISTRY: Dict[str, Provider] = {
    p.metadata.key: p for p in [
        # Search Providers
        serpapi_jobs_provider,
        serpapi_organic_provider,
        adzuna_provider,
        usajobs_provider,
        jooble_provider,
        careerjet_provider,
        themuse_provider,
        # Reasoning Providers
        openai_provider,
        gemini_provider,
        claude_provider,
        groq_provider,
        xai_provider,
    ]
}

def get_all_providers() -> List[Provider]:
    """Returns a list of all registered provider instances."""
    return list(_PROVIDER_REGISTRY.values())

def get_provider_by_key(key: str) -> Optional[Provider]:
    """Looks up a provider instance by its unique key."""
    return _PROVIDER_REGISTRY.get(key)

def get_providers_by_type(provider_type: ProviderType) -> List[Provider]:
    """Returns a list of providers of a specific type."""
    return [p for p in get_all_providers() if p.metadata.type == provider_type]

def get_provider_counts_by_type() -> Dict[str, int]:
    """Returns a summary count of providers by type."""
    counts = Counter(p.metadata.type.value for p in get_all_providers())
    return dict(counts)

__all__ = [
    "get_all_providers",
    "get_provider_by_key",
    "get_providers_by_type",
    "get_provider_counts_by_type",
    "Provider",
    "ProviderType",
    "SearchProvider",
    "ReasoningProvider",
]
