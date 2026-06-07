from typing import Dict, List, Any
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from .enums import TriggerType

class Batch(BaseModel):
    """

    Represents one complete ingestion run.
    """
    batch_id: str = Field(..., description="Unique ID for this batch.")
    batch_schema: str = "job_hunter_batch_v2"
    created_at: str
    trigger_type: TriggerType
    budget: Dict[str, Any] = Field(default_factory=dict)
    providers_used: List[str] = Field(default_factory=list)
    rules: Dict[str, Any] = Field(default_factory=dict)
    counts: Dict[str, int] = Field(default_factory=dict)
