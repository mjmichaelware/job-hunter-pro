"""Lever public Postings API — keyless per-company JSON.
Sweeps a configurable list of employer slugs (LEVER_BOARDS env overrides).
Default: a curated list of employers known to be on Lever, including national
employers that hire in SLC/Utah and strong remote-friendly companies.
Endpoint: https://api.lever.co/v0/postings/{slug}?mode=json
"""
import logging
import os
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

# Curated Lever board slugs (public, verified via jobs.lever.co/{slug}).
# Override entirely via LEVER_BOARDS=slug1,slug2 env var.
_DEFAULT_LEVER_BOARDS = [
    "adobe",            # major employer with SLC-area offices
    "salesforce",       # large national employer with UT presence
    "reddit",           # national, remote-friendly
    "klaviyo",          # national, remote-friendly marketing tech
    "rippling",         # national HR tech, remote-friendly
    "notion",           # national, remote-friendly
    "retool",           # national, remote-friendly dev tools
    "benchling",        # national, remote-friendly
    "openai",           # national AI company, remote-friendly roles
    "stripe",           # national fintech with remote roles
    "plaid",            # national fintech, remote-friendly
    "duolingo",         # national, remote-friendly
    "lyft",             # national with SLC-area driver/ops roles
    "squarespace",      # national, remote-friendly
    "intercom",         # national, remote-friendly SaaS
]

_env_override = os.environ.get("LEVER_BOARDS", "")
LEVER_BOARDS = [s.strip() for s in _env_override.split(",") if s.strip()] if _env_override else _DEFAULT_LEVER_BOARDS


class LeverProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="lever",
            label="Lever (ATS boards)",
            type=ProviderType.SEARCH,
            description="Keyless public ATS boards; sweeps curated employer slugs (override via LEVER_BOARDS).",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return "" if LEVER_BOARDS else "LEVER_BOARDS list is empty; set LEVER_BOARDS=slug1,slug2."

    def search(self, query: str) -> List[SearchResult]:
        terms = [w for w in query.lower().split() if len(w) > 3]
        results: List[SearchResult] = []
        for slug in LEVER_BOARDS:
            try:
                url = "https://api.lever.co/v0/postings/%s?mode=json" % slug
                resp = http_session.get(url, timeout=10)
                check_hard_failure(self.metadata.key, resp)
                resp.raise_for_status()
                for item in (resp.json() or []):
                    title = item.get("text", "")
                    if terms and not any(t in title.lower() for t in terms):
                        continue
                    loc = (item.get("categories") or {}).get("location", "")
                    results.append(SearchResult(
                        provider=self.metadata.key,
                        query=query,
                        title=title,
                        url=item.get("hostedUrl", ""),
                        snippet=loc,
                        source_name=slug,
                        published_date=str(item.get("createdAt", "")),
                        raw_json=item,
                        confidence=1.0,
                        cost_units=0.0,
                    ))
            except ProviderHardFailure:
                raise
            except Exception as e:
                logger.error("Lever board %s failed: %s", slug, e)
        return results


lever_provider = LeverProvider()
