"""Configuration package for data-driven search behavior.

This package holds declarative, no-I/O configuration that the rest of the
application reads. Keeping it separate from route code is what lets the system
grow to dozens of providers and domains without editing the HTTP layer.
"""

from .search_taxonomy import (
    BROAD_QUERY_TEMPLATES,
    DEFAULT_CITY,
    DEFAULT_POSTAL,
    DOMAIN_NEGATIVE_TERMS,
    list_domains,
)

__all__ = [
    "BROAD_QUERY_TEMPLATES",
    "DEFAULT_CITY",
    "DEFAULT_POSTAL",
    "DOMAIN_NEGATIVE_TERMS",
    "list_domains",
]
