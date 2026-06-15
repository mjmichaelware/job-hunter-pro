from dataclasses import dataclass
from typing import Optional
from ._base import Model


@dataclass
class ApiUsage(Model):
    """
    Records a single call to an external, billable API.
    """
    provider: str
    endpoint: str
    estimated_cost_units: float
    timestamp: str
    success: bool
    error: Optional[str] = None
