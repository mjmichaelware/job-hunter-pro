"""Ashby public Job Board API — keyless per-company JSON.
Sweeps a configurable list of employer slugs (set ASHBY_BOARDS=slug1,slug2).
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

ASHBY_BOARDS = [s.strip() for s in os.environ.get("ASHBY_BOARDS", "").split(",") if s.strip()]


class AshbyProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="ashby",
            label="Ashby (ATS boards)",
            type=ProviderType.SEARCH,
            description="Keyless public ATS boards; sweeps ASHBY_BOARDS employer slugs.",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return "" if ASHBY_BOARDS else "Set ASHBY_BOARDS=slug1,slug2 (employer slugs) to enable."

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
