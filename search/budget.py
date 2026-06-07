from typing import Dict

class BudgetGuard:
    def __init__(self, daily_budget: float, usage_tracker):
        self.daily_budget = daily_budget
        self.usage_tracker = usage_tracker

    def can_afford(self, provider_name: str, cost: float) -> bool:
        current_usage = self.usage_tracker.get_total_usage(provider_name)
        return (current_usage + cost) <= self.daily_budget

    def record_transaction(self, provider_name: str, cost: float):
        if not self.can_afford(provider_name, cost):
            raise ValueError(f"Budget exceeded for provider: {provider_name}")
        self.usage_tracker.record_usage(provider_name, cost)
