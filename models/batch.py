from dataclasses import dataclass, field
from typing import Dict, List, Any
from ._base import Model
from .enums import TriggerType


@dataclass
class Batch(Model):
    """
    Represents one complete ingestion run.
    """
    batch_id: str
    created_at: str
    trigger_type: TriggerType
    batch_schema: str = "job_hunter_batch_v2"
    budget: Dict[str, Any] = field(default_factory=dict)
    providers_used: List[str] = field(default_factory=list)
    rules: Dict[str, Any] = field(default_factory=dict)
    counts: Dict[str, int] = field(default_factory=dict)
