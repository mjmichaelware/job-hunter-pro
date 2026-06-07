from typing import Optional
from typing import Optional
from pydantic import BaseModel, Field, confloat

class JobSnapshot(BaseModel):
    """
    A snapshot of a Job's state at a specific moment in time (i.e., in a specific batch).
    This is an immutable record.
    """
    job_id: str # Foreign key to Job.canonical_key
    batch_id: str # Foreign key to Batch.id
    salary: Optional[str] = None
    description: Optional[str] = None
    commute_seconds: Optional[int] = None
    radius_miles: Optional[float] = None
    match_score: confloat(ge=0.0, le=100.0)
    review_score: confloat(ge=0.0, le=100.0)
    consistency_score: confloat(ge=0.0, le=100.0)
    risk_level: str
