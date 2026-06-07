from typing import Dict, Any

class UsageTracker:
    def __init__(self):
        self.usage_data = {}
        self.account_status = {}

    def record_usage(self, key: str, cost: float):
        self.usage_data[key] = self.usage_data.get(key, 0.0) + cost

    def get_total_usage(self, key: str) -> float:
        return self.usage_data.get(key, 0.0)

    def update_account_status(self, provider: str, status: Dict[str, Any]):
        self.account_status[provider] = status

    def get_account_status(self, provider: str) -> Dict[str, Any]:
        return self.account_status.get(provider, {})
