from dataclasses import dataclass
from typing import Optional
from ._base import Model
from .enums import ApplicationStatus


@dataclass
class Application(Model):
    """
    Tracks a user's application to a specific job.
    This is part of Michael's personal application tracker.
    """
    job_id: str
    created_at: str
    updated_at: str
    status: str = ApplicationStatus.DISCOVERED.value
    notes: Optional[str] = None
