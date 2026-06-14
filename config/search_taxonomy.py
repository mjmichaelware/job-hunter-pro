"""Search taxonomy: the single source of truth for what we search for.

Design goals
------------
1. Broad, all-jobs discovery is FIRST-CLASS and the DEFAULT. Food service is NOT
   the governing universe anymore; it is one optional domain preset among many.
2. Adding or expanding a domain is a data edit here (or in ``industries/``),
   never a code edit in the API route layer.
3. No I/O. Pure data + tiny pure helpers. Safe to import anywhere.

The per-domain query banks and keyword sets live in the ``industries/`` package
(``industries.get_route(key)``). This module adds the broad, cross-industry
query layer that the old code never had, plus light negative-term hints used
only when a caller explicitly opts into a domain preset.
"""

from __future__ import annotations

from typing import Dict, List

DEFAULT_CITY = "Salt Lake City, UT"
DEFAULT_POSTAL = "84115"

# Broad, high-recall query seeds. Intentionally industry-neutral so that the
# default discovery run surfaces jobs from every working provider rather than
# only restaurants. ``{city}`` and ``{postal}`` are filled by the query builder.
BROAD_QUERY_TEMPLATES: List[str] = [
    "jobs near {postal} {city}",
    "hiring now {city}",
    "full time jobs {city}",
    "part time jobs {city}",
    "entry level jobs {city}",
    "warehouse jobs {city}",
    "customer service jobs {city}",
    "retail jobs {city}",
    "administrative assistant jobs {city}",
    "healthcare support jobs {city}",
    "driver jobs {city}",
    "general labor jobs {city}",
    "maintenance jobs {city}",
    "call center jobs {city}",
]

# Optional negative-term hints applied ONLY when a domain preset is explicitly
# selected. In broad mode nothing here is used, so broad mode never rejects a
# job for being "the wrong industry". The authoritative per-industry term sets
# remain in ``industries/``; this is a small convenience mirror for callers that
# do not want to import the industries package.
DOMAIN_NEGATIVE_TERMS: Dict[str, List[str]] = {
    "food_service": [
        "registered nurse", "software engineer", "cdl", "forklift",
    ],
}


def list_domains() -> List[str]:
    """Domain keys that callers may use as an explicit preset.

    Sourced from the industries registry when available so the two stay in sync,
    with a static fallback if the registry cannot be imported.
    """
    try:
        from industries import list_industries

        return list(list_industries())
    except Exception:
        return ["food_service", "hospitality", "sales", "customer_service", "care_social", "retail_ops"]


def broad_queries(city: str = DEFAULT_CITY, postal: str = DEFAULT_POSTAL) -> List[str]:
    """Render the broad query templates for a location."""
    city = (city or DEFAULT_CITY).strip()
    postal = (postal or DEFAULT_POSTAL).strip()
    out: List[str] = []
    for template in BROAD_QUERY_TEMPLATES:
        try:
            out.append(template.format(city=city, postal=postal).strip())
        except Exception:
            out.append(template)
    return out
