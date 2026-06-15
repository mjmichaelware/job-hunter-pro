from dataclasses import dataclass
from typing import Optional
from ._base import Model


@dataclass
class JobSnapshot(Model):
    """
    A snapshot of a Job's state at a specific moment in time (i.e., in a specific batch).
    This is an immutable record.

    Scores are 0.0–100.0 heuristics; they are clamped to that range in
    ``__post_init__`` rather than raising, so an out-of-range score never
    drops a real job.
    """
    job_id: str  # Foreign key to Job.canonical_key
    batch_id: str  # Foreign key to Batch.id
    match_score: float
    review_score: float
    consistency_score: float
    risk_level: str
    salary: Optional[str] = None
    description: Optional[str] = None
    commute_seconds: Optional[int] = None
    radius_miles: Optional[float] = None

    def __post_init__(self) -> None:
        for name in ("match_score", "review_score", "consistency_score"):
            value = getattr(self, name)
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = 0.0
            setattr(self, name, max(0.0, min(100.0, value)))
