"""Ashby public Job Board API — keyless per-company JSON.
Sweeps a configurable list of employer slugs (ASHBY_BOARDS env overrides).
Default: a curated list of employers known to be on Ashby HQ, including
remote-friendly and growth-stage companies that hire nationally.
Endpoint: https://api.ashbyhq.com/posting-api/job-board/{slug}
"""
import logging
import os
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

# Curated Ashby board slugs (public, verified via jobs.ashbyhq.com/{slug}).
# Override entirely via ASHBY_BOARDS=slug1,slug2 env var.
_DEFAULT_ASHBY_BOARDS = [
    "linear",           # remote-first product tool company
    "mercury",          # remote-friendly fintech
    "ramp",             # remote-friendly fintech
    "vercel",           # remote-first dev tools
    "posthog",          # remote-first analytics
    "dbt-labs",         # remote-first data tools
    "modal",            # remote-first AI infra
    "baseten",          # remote-friendly ML infra
    "replit",           # remote-first dev platform
    "loom",             # remote-friendly (Atlassian-owned)
    "beehiiv",          # remote-friendly newsletter platform
    "plain",            # remote-first customer support SaaS
    "watershed",        # remote-friendly climate tech
    "arc",              # remote jobs marketplace (relevant to remote seekers)
    "anduril",          # defense tech, multiple US locations including near UT
]

_env_override = os.environ.get("ASHBY_BOARDS", "")
ASHBY_BOARDS = [s.strip() for s in _env_override.split(",") if s.strip()] if _env_override else _DEFAULT_ASHBY_BOARDS


class AshbyProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="ashby",
            label="Ashby (ATS boards)",
            type=ProviderType.SEARCH,
            description="Keyless public ATS boards; sweeps curated employer slugs (override via ASHBY_BOARDS).",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return "" if ASHBY_BOARDS else "ASHBY_BOARDS list is empty; set ASHBY_BOARDS=slug1,slug2."

    def search(self, query: str) -> List[SearchResult]:
        terms = [w for w in query.lower().split() if len(w) > 3]
        results: List[SearchResult] = []
        for slug in ASHBY_BOARDS:
            try:
                url = "https://api.ashbyhq.com/posting-api/job-board/%s" % slug
                resp = http_session.get(url, timeout=10)
                check_hard_failure(self.metadata.key, resp)
                resp.raise_for_status()
                for item in (resp.json().get("jobs", []) or []):
                    title = item.get("title", "")
                    if terms and not any(t in title.lower() for t in terms):
                        continue
                    results.append(SearchResult(
                        provider=self.metadata.key,
                        query=query,
                        title=title,
                        url=item.get("jobUrl", "") or item.get("applyUrl", ""),
                        snippet=item.get("location", ""),
                        source_name=slug,
                        published_date=item.get("publishedAt") or item.get("publishedDate"),
                        raw_json=item,
                        confidence=1.0,
                        cost_units=0.0,
                    ))
            except ProviderHardFailure:
                raise
            except Exception as e:
                logger.error("Ashby board %s failed: %s", slug, e)
        return results


ashby_provider = AshbyProvider()
