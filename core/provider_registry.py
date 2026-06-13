from __future__ import annotations
import logging
from typing import Dict, List, Optional

from providers.base import Provider, ProviderStatus, ProviderType

logger = logging.getLogger(__name__)

class ProviderRegistry:
    """A stateful registry for managing the runtime status of all providers."""

    def __init__(self, providers: List[Provider]):
        self._providers: Dict[str, Provider] = {p.metadata.key: p for p in providers}
        self._initialize_status()

    def _initialize_status(self):
        """Sets the initial status of each provider based on its availability."""
        for key, provider in self._providers.items():
            try:
                if provider.is_available():
                    provider.metadata.status = ProviderStatus.AVAILABLE
                else:
                    provider.metadata.status = ProviderStatus.DORMANT
            except Exception as e:
                logger.error(f"Failed to check availability for provider {key}: {e}")
                provider.metadata.status = ProviderStatus.DISABLED

    def get_provider(self, key: str) -> Optional[Provider]:
        """Gets a single provider by its key."""
        return self._providers.get(key)

    def get_all_providers(self) -> List[Provider]:
        """Returns a list of all provider instances, regardless of status."""
        return list(self._providers.values())

    def get_providers_by_capability(
        self,
        required_capabilities: List[str],
        allowed_statuses: List[ProviderStatus] = [ProviderStatus.AVAILABLE],
    ) -> List[Provider]:
        """
        Gets a list of providers that have all the required capabilities
        and one of the allowed statuses.
        """
        active_providers = []
        for provider in self._providers.values():
            if provider.metadata.status not in allowed_statuses:
                continue

            has_all_caps = all(
                getattr(provider.metadata, cap, False) for cap in required_capabilities
            )

            if has_all_caps:
                active_providers.append(provider)
        return active_providers

    def update_provider_status(self, key: str, status: ProviderStatus):
        """Updates the runtime status of a specific provider."""
        provider = self.get_provider(key)
        if provider:
            logger.info(f"Updating status for provider '{key}' to '{status.value}'")
            provider.metadata.status = status
        else:
            logger.warning(f"Attempted to update status for unknown provider '{key}'")

    def get_all_provider_statuses(self) -> List[Dict]:
        """Returns a list of metadata for all registered providers for status reporting."""
        return [p.metadata.__dict__ for p in self._providers.values()]

provider_registry: Optional[ProviderRegistry] = None

def initialize_registry():
    """Initializes the provider registry singleton."""
    global provider_registry
    if provider_registry is None:
        from providers import get_all_providers as get_static_providers
        provider_registry = ProviderRegistry(providers=get_static_providers())
        logger.info("ProviderRegistry initialized.")

def get_provider_registry() -> ProviderRegistry:
    """Global accessor for the provider registry singleton."""
    if provider_registry is None:
        raise RuntimeError("ProviderRegistry has not been initialized. Call initialize_registry() at startup.")
    return provider_registry
