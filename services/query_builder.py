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
    max_queries: Optional[int] = 24,
    extra_terms: Optional[List[str]] = None,
) -> List[str]:
    """Build the query bank for a discovery run.

    Args:
        mode: ``broad`` (default) or an industry/domain key.
        city / postal: location seeds for broad templates.
        max_queries: hard cap on returned queries (protects provider fanout).
        extra_terms: optional user keyword(s) promoted to the front of the bank.
    """
    mode = (mode or BROAD_MODE).strip().lower()
    queries: List[str] = []

    if extra_terms:
        for term in extra_terms:
            term = (term or "").strip()
            if term:
                queries.append(f"{term} jobs {city}")

    if mode == BROAD_MODE or mode == "all":
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
    if max_queries and max_queries > 0:
        return unique[:max_queries]
    return unique
