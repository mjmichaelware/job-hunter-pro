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
        """
        Determines if a provider call can be afforded.
        Each provider declares its own budget_class in metadata; only
        quota-limited classes are gated. Free providers are always affordable.
        """
        budget_class = self._budget_class(provider_key)

        if budget_class == "serpapi_quota":
            if not Config.SERPAPI_BUDGET_MODE:
                return True

            account_status = self.usage_tracker.get_account_status("serpapi")
            if not account_status:
                logger.debug(f"SerpAPI status unknown. Allowing '{provider_key}' call.")
                return True

            searches_left = account_status.get("total_searches_left", 0)
            if searches_left <= Config.SERPAPI_MIN_SEARCHES_LEFT:
                logger.warning(f"Budget Lock: SerpAPI quota low ({searches_left}). Blocking '{provider_key}'.")
                return False

            return True

        # Free / unmetered providers are always affordable.
        return True

    def record_transaction(self, provider_key: str, cost: float = 1.0):
        """
        Records the successful completion of a provider call.
        """
        self.usage_tracker.record_usage(provider_key, cost)
