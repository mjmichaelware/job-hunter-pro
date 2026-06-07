from typing import Optional
from typing import Optional
from pydantic import BaseModel, Field
from .enums import ApplicationStatus

class Application(BaseModel):
    """
    Tracks a user's application to a specific job.
    This is part of Michael's personal application tracker.
    """
    job_id: str = Field(..., description="Foreign key to the Job entity.")
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    notes: Optional[str] = None
    created_at: str
    updated_at: str
