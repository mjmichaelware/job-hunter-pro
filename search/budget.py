import logging
from typing import Dict
from core import Config

logger = logging.getLogger(__name__)

class BudgetGuard:
    def __init__(self, usage_tracker):
        self.usage_tracker = usage_tracker

    def can_afford(self, provider_key: str, cost: float = 1.0) -> bool:
        """
        Determines if a provider call can be afforded.
        Gated by SerpAPI account status for SerpAPI-based providers.
        Always allows free/keyless providers if enabled.
        """
        # Free/Keyless providers are always affordable if enabled
        if provider_key in ["themuse", "usajobs"]:
            return True

        # SerpAPI-based providers
        if provider_key.startswith("serpapi"):
            # Check if budget mode is even active
            if not Config.SERPAPI_BUDGET_MODE:
                return True

            # If we don't know the status yet, assume affordable but warn
            # In a real system, we'd fetch this from cache or a dedicated usage service
            # For this local backend, we'll check the usage_tracker if it has account info
            account_status = self.usage_tracker.get_account_status("serpapi")
            if not account_status:
                logger.debug(f"SerpAPI status unknown. Allowing '{provider_key}' call.")
                return True
            
            searches_left = account_status.get("total_searches_left", 0)
            if searches_left <= Config.SERPAPI_MIN_SEARCHES_LEFT:
                logger.warning(f"Budget Lock: SerpAPI quota low ({searches_left}). Blocking '{provider_key}'.")
                return False
            
            return True

        # Default to true for others unless specifically gated
        return True

    def record_transaction(self, provider_key: str, cost: float = 1.0):
        """
        Records the successful completion of a provider call.
        """
        self.usage_tracker.record_usage(provider_key, cost)
