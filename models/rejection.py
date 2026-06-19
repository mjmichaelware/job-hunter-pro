from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from ._base import Model


@dataclass
class Rejection(Model):
    """
    Records why a raw search result was rejected from a batch.
    """
    batch_id: str
    reason: str
    raw_result_id: Optional[str] = None
    job_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
