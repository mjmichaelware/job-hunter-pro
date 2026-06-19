"""Lever public Postings API — keyless per-company JSON.
Sweeps a configurable list of employer slugs (set LEVER_BOARDS=slug1,slug2).
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

LEVER_BOARDS = [s.strip() for s in os.environ.get("LEVER_BOARDS", "").split(",") if s.strip()]


class LeverProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="lever",
            label="Lever (ATS boards)",
            type=ProviderType.SEARCH,
            description="Keyless public ATS boards; sweeps LEVER_BOARDS employer slugs.",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return "" if LEVER_BOARDS else "Set LEVER_BOARDS=slug1,slug2 (employer slugs) to enable."

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
