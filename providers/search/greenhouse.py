"""Greenhouse public Boards API — keyless per-company JSON.
Sweeps a configurable list of employer slugs (set GREENHOUSE_BOARDS=slug1,slug2),
e.g. local SLC employers that host on Greenhouse. No secret required.
Endpoint: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
"""
import logging
import os
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

GREENHOUSE_BOARDS = [s.strip() for s in os.environ.get("GREENHOUSE_BOARDS", "").split(",") if s.strip()]


class GreenhouseProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="greenhouse",
            label="Greenhouse (ATS boards)",
            type=ProviderType.SEARCH,
            description="Keyless public ATS boards; sweeps GREENHOUSE_BOARDS employer slugs.",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True  # keyless; yields results once GREENHOUSE_BOARDS is configured

    def disabled_reason(self) -> str:
        return "" if GREENHOUSE_BOARDS else "Set GREENHOUSE_BOARDS=slug1,slug2 (employer slugs) to enable."

    def search(self, query: str) -> List[SearchResult]:
        terms = [w for w in query.lower().split() if len(w) > 3]
        results: List[SearchResult] = []
        for slug in GREENHOUSE_BOARDS:
            try:
                url = "https://boards-api.greenhouse.io/v1/boards/%s/jobs?content=true" % slug
                resp = http_session.get(url, timeout=10)
                check_hard_failure(self.metadata.key, resp)
                resp.raise_for_status()
                for item in (resp.json().get("jobs", []) or []):
                    title = item.get("title", "")
                    if terms and not any(t in title.lower() for t in terms):
                        continue
                    loc = (item.get("location") or {}).get("name", "")
                    results.append(SearchResult(
                        provider=self.metadata.key,
                        query=query,
                        title=title,
                        url=item.get("absolute_url", ""),
                        snippet=loc,
                        source_name=slug,
                        published_date=item.get("updated_at"),
                        raw_json=item,
                        confidence=1.0,
                        cost_units=0.0,
                    ))
            except ProviderHardFailure:
                raise
            except Exception as e:
                logger.error("Greenhouse board %s failed: %s", slug, e)
        return results


greenhouse_provider = GreenhouseProvider()
