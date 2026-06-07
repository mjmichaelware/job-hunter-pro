class UsageTracker:
    def __init__(self):
        self.usage_data = {}

    def record_usage(self, key: str, cost: float):
        self.usage_data[key] = self.usage_data.get(key, 0.0) + cost

    def get_total_usage(self, key: str) -> float:
        return self.usage_data.get(key, 0.0)
