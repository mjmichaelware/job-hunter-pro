"""Service layer: decoupled business logic that sits between providers and routes.

Each module has a single concern so the system can scale to many providers and
domains without entangling the HTTP layer:

- ``query_builder``   : turn a discovery mode into a deduped query bank
- ``provider_status`` : provider enable/disable + per-run quarantine policy
- ``filtering``       : apply ONLY the filters the user explicitly set
- ``job_aggregator``  : canonical dedupe + accepted/rejected partitioning

These modules are import-safe (no I/O at import time) so route code can depend
on them defensively.
"""

__all__ = [
    "query_builder",
    "provider_status",
    "filtering",
    "job_aggregator",
]
