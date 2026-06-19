import logging
from typing import Dict
from core import Config

logger = logging.getLogger(__name__)

class BudgetGuard:
    def __init__(self, usage_tracker):
        self.usage_tracker = usage_tracker

    def _budget_class(self, provider_key: str) -> str:
        """Resolve a provider's budget class from its own metadata (no central
        name list). Falls back to the serpapi key-prefix heuristic if the
        provider isn't in the registry."""
        try:
            from providers import get_provider_by_key

            provider = get_provider_by_key(provider_key)
            if provider is not None:
                cls = getattr(provider.metadata, "budget_class", None)
                if cls:
                    return str(cls)
        except Exception:
            pass
        return "serpapi_quota" if str(provider_key).startswith("serpapi") else "free"

    def can_afford(self, provider_key: str, cost: float = 1.0) -> bool:
        """All providers are affordable — SerpAPI quota guard removed.
        New free providers are in play; gating is no longer needed."""
        return True

    def record_transaction(self, provider_key: str, cost: float = 1.0):
        """
        Records the successful completion of a provider call.
        """
        self.usage_tracker.record_usage(provider_key, cost)
