from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class Rejection(BaseModel):
    """
    Records why a raw search result was rejected from a batch.
    """
    batch_id: str = Field(..., description="The batch in which this rejection occurred.")
    raw_result_id: Optional[str] = Field(None, description="Foreign key to the raw result, if stored.")
    job_id: Optional[str] = Field(None, description="Foreign key to a job, if it was resolved before rejection.")
    reason: str = Field(..., description="The primary reason for rejection (from RejectionReason enum).")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details about the rejection.")
