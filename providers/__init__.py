"""Provider registry — AUTO-DISCOVERED.

Decoupling goal: adding a new job API (#8 ... #50) is a one-file operation. Drop
a module in ``providers/search/`` (or ``providers/reasoning/``) that defines a
concrete ``Provider`` instance, and it registers itself here automatically. No
edits to this file, no central import list, no merge conflicts on a shared file.

Rules that make a 50-API swarm safe:
- Every ``providers/search/*.py`` and ``providers/reasoning/*.py`` module is
  imported in isolation; a single broken provider file is skipped and logged,
  never crashing the rest of the swarm.
- Any module-level value that is a concrete ``Provider`` instance is registered
  by its ``metadata.key`` (last one wins on key collision).
- Files starting with ``_`` and ``base`` are ignored.
"""

import importlib
import logging
import pkgutil
from collections import Counter
from typing import Dict, List, Optional

from .base import Provider, ProviderType, SearchProvider, ReasoningProvider

logger = logging.getLogger(__name__)

# Packages scanned for provider modules. Add a new sub-package here only if you
# introduce a brand-new provider *category*; individual providers never need it.
_PROVIDER_PACKAGES = ("providers.search", "providers.reasoning")


def _discover_providers() -> Dict[str, Provider]:
    registry: Dict[str, Provider] = {}
    for pkg_name in _PROVIDER_PACKAGES:
        try:
            package = importlib.import_module(pkg_name)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Provider package %s failed to import: %s", pkg_name, exc)
            continue

        for _finder, mod_name, _ispkg in pkgutil.iter_modules(package.__path__):
            if mod_name.startswith("_") or mod_name == "base":
                continue
            full_name = f"{pkg_name}.{mod_name}"
            try:
                module = importlib.import_module(full_name)
            except Exception as exc:
                # One bad provider must never take down the swarm.
                logger.warning("Skipping provider module %s (import failed): %s", full_name, exc)
                continue

            for value in vars(module).values():
                if isinstance(value, Provider):
                    try:
                        key = value.metadata.key
                    except Exception:
                        continue
                    registry[key] = value
    return registry


# The single source of truth, built once at import.
_PROVIDER_REGISTRY: Dict[str, Provider] = _discover_providers()


def get_all_providers() -> List[Provider]:
    """Returns a list of all auto-discovered provider instances."""
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


def reload_providers() -> Dict[str, Provider]:
    """Re-run discovery (useful after adding a provider file at runtime/tests)."""
    global _PROVIDER_REGISTRY
    _PROVIDER_REGISTRY = _discover_providers()
    return _PROVIDER_REGISTRY


__all__ = [
    "get_all_providers",
    "get_provider_by_key",
    "get_providers_by_type",
    "get_provider_counts_by_type",
    "reload_providers",
    "Provider",
    "ProviderType",
    "SearchProvider",
    "ReasoningProvider",
]
