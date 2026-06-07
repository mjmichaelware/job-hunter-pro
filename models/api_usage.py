from typing import Optional
from pydantic import BaseModel, Field

class ApiUsage(BaseModel):
    """
    Records a single call to an external, billable API.
    """
    provider: str
    endpoint: str
    estimated_cost_units: float
    timestamp: str
    success: bool
    error: Optional[str] = None
