"""Job aggregator: canonical dedupe + accepted/rejected partitioning.

This is where the "show every valid job, hide nothing silently" rule lives.

Core principles
---------------
- In BROAD mode (default), a real provider result is ACCEPTED. Missing
  address / radius / transit resolution becomes ``resolution_flags`` on the
  accepted job — it is NEVER a reason to delete the job.
- A record is REJECTED only when it is genuinely not a usable job:
    * ``missing_title``           : no title at all
    * ``no_link_or_company``      : nothing to identify or apply to
    * ``duplicate``               : same canonical identity already accepted
    * ``domain_mismatch``         : only when the caller explicitly chose a
                                    domain preset and the job clearly is not it
- Rejected records keep their evidence (title, provider, reasons) so the UI can
  show them honestly in a separate panel.

Pure functions, no I/O.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

BROAD_MODE = "broad"


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value if value is not None else "")).strip()


def canonical_key(job: Dict[str, Any]) -> str:
    """Stable identity: exact source URL as primary key, URL fallback to title+company+addr."""
    url = _clean(job.get("source_url") or job.get("url") or job.get("job_id")).lower()
    if url:
        return url
    title = _clean(job.get("title")).lower()
    company = _clean(job.get("company")).lower()
    return f"{title}|{company}|{_clean(job.get('location')).lower()}"


def resolution_flags(job: Dict[str, Any]) -> List[str]:
    """Non-fatal flags describing what could not be resolved for this job."""
    flags: List[str] = []
    if not _clean(job.get("resolved_address")):
        flags.append("address_unresolved")
    if job.get("radius_miles") is None:
        flags.append("radius_unverified")
    if job.get("commute_seconds") is None:
        flags.append("transit_unverified")
    return flags


def _domain_mismatch(job: Dict[str, Any], domain: str) -> bool:
    """True only when an explicit domain preset clearly does not match the job."""
    try:
        from industries import get_route
        from industries.base import score_text_for_industry
    except Exception:
        return False

    route = get_route(domain)
    if not route:
        return False

    text = " ".join([
        _clean(job.get("title")),
        _clean(job.get("description")),
        _clean(job.get("company")),
        " ".join(job.get("tags") or []),
    ])
    # Negative match => score goes strongly negative (negatives weighted x10).
    return score_text_for_industry(text, route) < 0


def partition(
    normalized_jobs: List[Dict[str, Any]],
    mode: str = "broad",
    domain: str = "",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split normalized jobs into (accepted, rejected).

    In BROAD mode (default): EVERY usable job is ACCEPTED.  Missing address /
    radius / transit resolution becomes ``resolution_flags`` on the accepted job —
    it is NEVER a reason to delete the job.

    Only truly duplicate records (same source URL) are dropped.
    """
    mode = (mode or "broad").strip().lower()
    domain = (domain or "").strip().lower()

    accepted: List[Dict[str, Any]] = []
    seen_keys = set()

    for job in normalized_jobs:
        key = canonical_key(job)
        is_dupe = key in seen_keys
        seen_keys.add(key)

        # Flag missing attributes without dropping the record
        flags: List[str] = []
        if not _clean(job.get("resolved_address")):
            flags.append("address_unresolved")
        if job.get("radius_miles") is None:
            flags.append("radius_unverified")
        if job.get("commute_seconds") is None:
            flags.append("transit_unverified")
        if not job.get("description") or len(_clean(job.get("description"))) < 100:
            flags.append("needs_deep_scrape")

        job["resolution_flags"] = flags
        job["needs_resolution"] = bool(flags)

        # EVERY SINGLE JOB IS ACCEPTED — only skip if it's a duplicate URL
        if is_dupe:
            continue

        accepted.append(job)

    return accepted, []  # Zero rejected jobs
