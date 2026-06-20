"""Query builder: turn a discovery mode into a deduped, capped query bank.

Modes
-----
- ``broad`` (DEFAULT): industry-neutral high-recall seeds PLUS a sample of every
  registered industry route's queries, so a default run reaches all providers
  across all domains. This is what makes "all jobs" first-class.
- ``<domain key>`` (e.g. ``food_service``): that domain's queries first, with a
  few broad seeds appended for recall. Domain presets are explicit and optional.

No I/O. The industries registry is read for domain queries; if it is unavailable
the broad seeds still work, so discovery never hard-depends on it.
"""

from __future__ import annotations

import os
from typing import List, Optional

from config.search_taxonomy import DEFAULT_CITY, DEFAULT_POSTAL, broad_queries

BROAD_MODE = "broad"


def _domain_queries(domain: str) -> List[str]:
    try:
        from industries import get_route

        route = get_route(domain)
        if route and route.queries:
            return list(route.queries)
    except Exception:
        pass
    return []


def _all_industry_queries(per_route: int = 3) -> List[str]:
    """A small sample of queries from every industry route (broad recall)."""
    out: List[str] = []
    try:
        from industries import get_all_routes

        for route in get_all_routes():
            for q in list(route.queries)[:per_route]:
                out.append(q)
    except Exception:
        pass
    return out


def _dedupe(queries: List[str]) -> List[str]:
    seen = set()
    unique: List[str] = []
    for q in queries:
        key = (q or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(q.strip())
    return unique


def build_queries(
    mode: str = BROAD_MODE,
    city: str = DEFAULT_CITY,
    postal: str = DEFAULT_POSTAL,
    max_queries: Optional[int] = int(os.environ.get("MAX_QUERIES", "50")),
    extra_terms: Optional[List[str]] = None,
    offset: int = 0,
) -> List[str]:
    """Build the query bank for a discovery run.

    Args:
        mode: ``broad`` (default) or an industry/domain key.
        city / postal: location seeds for broad templates.
        max_queries: hard cap on returned queries. When ``None`` or ``<=0``
            ALL unique queries are returned (no cap). Defaults to the
            ``MAX_QUERIES`` environment variable (default ``"50"``).
        extra_terms: optional user keyword(s) promoted to the front of the
            bank. These are always included and are not subject to the
            rotation/cap.
        offset: when a cap applies, rotate the deduplicated bank by this many
            positions before slicing so that successive runs sample different
            keyword slices. The ``extra_terms`` front section is not rotated.
            ``offset=0`` gives the same result as the original behaviour.
    """
    mode = (mode or BROAD_MODE).strip().lower()

    # Collect extra_terms first — these are always promoted to the front and
    # are not subject to rotation or cap.
    promoted: List[str] = []
    if extra_terms:
        for term in extra_terms:
            term = (term or "").strip()
            if term:
                promoted.append(f"{term} jobs {city}")

    queries: List[str] = []
    if mode in ("local", "near_me", "nearby"):
        # Location-biased recall: every seed is anchored to the city/postal so the
        # keyword-driven boards return physically-local jobs (which then resolve a
        # Google place + commute), instead of remote-heavy listings.
        base = broad_queries(city, postal) + _all_industry_queries(per_route=3)
        anchor = city.split(",")[0].strip()
        for q in base:
            ql = (q or "").strip()
            if not ql:
                continue
            queries.append(ql if anchor.lower() in ql.lower() else f"{ql} {anchor} {postal}")
    elif mode == BROAD_MODE or mode == "all":
        queries.extend(broad_queries(city, postal))
        queries.extend(_all_industry_queries(per_route=3))
    else:
        domain_q = _domain_queries(mode)
        if domain_q:
            queries.extend(domain_q)
        # Always append a few broad seeds so a domain preset never collapses to
        # zero recall if the domain bank is thin.
        queries.extend(broad_queries(city, postal)[:4])
        if not domain_q:
            # Unknown domain key: fall back to broad behavior rather than empty.
            queries.extend(_all_industry_queries(per_route=2))

    unique = _dedupe(queries)

    if not max_queries or max_queries <= 0:
        # No cap — return promoted + full bank.
        return _dedupe(promoted + unique)

    # Apply rotation to the main bank before slicing, then prepend promoted.
    if unique:
        n = len(unique)
        start = offset % n
        rotated = unique[start:] + unique[:start]
    else:
        rotated = unique

    # Slots for the main bank after reserving space for promoted entries.
    # promoted entries are de-duplicated into their own list first so we do
    # not accidentally cut the cap below len(promoted).
    promoted_deduped = _dedupe(promoted)
    remaining_cap = max(0, max_queries - len(promoted_deduped))
    return _dedupe(promoted_deduped + rotated[:remaining_cap])
