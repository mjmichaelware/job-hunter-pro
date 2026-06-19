"""Filtering: apply ONLY the filters the user explicitly set.

This is the antidote to the original bug where the UI silently applied strict
default filters and zeroed out a perfectly good result set. Here, a filter
narrows results ONLY when the caller passes a real, non-empty value. Absent or
blank params mean "do not narrow" — broad-by-default.

Pure functions, no I/O, no request globals.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _num(value: Any) -> Optional[float]:
    if value in (None, "", "all"):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _text(value: Any) -> str:
    return str(value if value is not None else "").strip().lower()


def _job_field(job: Dict[str, Any], keys, default=None):
    for key in keys:
        val = job.get(key)
        if val not in (None, ""):
            return val
    return default


def apply_filters(jobs: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Narrow ``jobs`` by only the explicitly-provided ``params``.

    Supported (all optional):
      min_rating, max_radius, max_transit (minutes), min_score (review score),
      min_match, industry, provider, role, house, q (keyword).
    """
    min_rating = _num(params.get("min_rating"))
    max_radius = _num(params.get("max_radius"))
    max_transit = _num(params.get("max_transit"))
    min_score = _num(params.get("min_score"))
    min_match = _num(params.get("min_match"))
    industry = _text(params.get("industry"))
    provider = _text(params.get("provider"))
    role = _text(params.get("role"))
    house = _text(params.get("house"))
    q = _text(params.get("q"))

    out: List[Dict[str, Any]] = []
    for job in jobs:
        if min_rating is not None:
            rating = _num(_job_field(job, ["google_rating", "rating", "place_rating"]))
            if rating is None or rating < min_rating:
                continue
        if max_radius is not None:
            radius = _num(_job_field(job, ["radius_miles", "distance_miles", "haversine_radius_miles"]))
            # Only exclude when we actually know the radius and it exceeds the cap.
            if radius is not None and radius > max_radius:
                continue
        if max_transit is not None:
            commute = _num(_job_field(job, ["commute_seconds", "transit_seconds", "commute_matrix_seconds"]))
            if commute is not None and commute / 60.0 > max_transit:
                continue
        if min_score is not None:
            review = _num(_job_field(job, ["review_score", "review_heuristic_score"]))
            if review is None or review < min_score:
                continue
        if min_match is not None:
            match = _num(_job_field(job, ["match", "match_score", "score"]))
            if match is not None and match < min_match:
                continue
        if industry and industry != "all":
            job_industry = _text(_job_field(job, ["industry", "industry_key", "role_family"]))
            if job_industry and job_industry != industry:
                continue
        if provider and provider != "all":
            job_provider = _text(_job_field(job, ["provider", "source", "via", "_provider"]))
            if job_provider and provider not in job_provider:
                continue
        if role and role != "all":
            haystack = " ".join([
                _text(job.get("title")),
                " ".join(job.get("tags") or []),
            ])
            if role not in haystack:
                continue
        if house and house != "all":
            if _text(job.get("role_family")) != house:
                continue
        if q:
            haystack = " ".join([
                _text(job.get("title")),
                _text(_job_field(job, ["company", "restaurant_name"])),
                _text(_job_field(job, ["resolved_address", "location"])),
                _text(job.get("description")),
                " ".join(job.get("tags") or []),
            ])
            if q not in haystack:
                continue
        out.append(job)
    return out
