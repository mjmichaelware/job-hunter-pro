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
    """Stable identity: title + normalized place/address, with URL/company fallback."""
    title = _clean(job.get("title")).lower()
    name = _clean(job.get("restaurant_name") or job.get("resolved_place_name") or job.get("company")).lower()
    addr = _clean(job.get("resolved_address") or job.get("location")).lower()
    if not name and not addr:
        uniq = _clean(
            job.get("source_url") or job.get("url") or job.get("company") or job.get("job_id")
        ).lower()
        return f"{title}|{uniq}"
    return f"{title}|{name}|{addr}"


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
    mode: str = BROAD_MODE,
    domain: str = "",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split normalized jobs into (accepted, rejected).

    ``mode`` ``broad`` accepts every usable job. A non-broad ``mode`` (or an
    explicit ``domain``) additionally rejects clear domain mismatches.
    """
    mode = (mode or BROAD_MODE).strip().lower()
    domain = (domain or (mode if mode != BROAD_MODE else "")).strip().lower()

    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    seen_keys = set()

    for job in normalized_jobs:
        reasons: List[str] = []
        title = _clean(job.get("title"))
        link = _clean(job.get("source_url") or job.get("url"))
        company = _clean(job.get("company") or job.get("restaurant_name"))

        if not title or title.lower() in {"untitled job", "untitled role"}:
            reasons.append("missing_title")
        if not link and not company:
            reasons.append("no_link_or_company")
        if domain and _domain_mismatch(job, domain):
            reasons.append(f"domain_mismatch_{domain}")

        key = canonical_key(job)
        is_dupe = key in seen_keys

        if reasons or is_dupe:
            if is_dupe and "duplicate" not in reasons:
                reasons.append("duplicate")
            rejected.append({
                "provider": job.get("_provider") or job.get("provider") or job.get("source") or job.get("via"),
                "query": job.get("_query_used") or job.get("place_query_used"),
                "title": job.get("title"),
                "company": job.get("company"),
                "restaurant_name": job.get("restaurant_name"),
                "resolved_address": job.get("resolved_address"),
                "commute_label": job.get("commute_label"),
                "radius_label": job.get("radius_label"),
                "tags": job.get("tags"),
                "source_url": job.get("source_url") or job.get("url"),
                "reasons": reasons,
            })
            continue

        seen_keys.add(key)
        flags = resolution_flags(job)
        job["resolution_flags"] = flags
        job["needs_resolution"] = bool(flags)
        accepted.append(job)

    return accepted, rejected
