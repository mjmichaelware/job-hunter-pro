from .provider_registry import ProviderRegistry, get_provider_registry

# Initialize the registry singleton on startup
from providers import get_all_providers as get_static_providers
from .provider_registry import provider_registry as registry_singleton

if registry_singleton is None:
    registry_singleton = ProviderRegistry(providers=get_static_providers())

# Make get_provider_registry easily accessible from the core package
__all__ = ["get_provider_registry"]
