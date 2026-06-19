"""Arbeitnow Job Board — keyless public JSON API. https://www.arbeitnow.com"""
import logging
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)


class ArbeitnowProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="arbeitnow",
            label="Arbeitnow",
            type=ProviderType.SEARCH,
            description="Keyless public job-board API (remote + listings).",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def search(self, query: str) -> List[SearchResult]:
        terms = [w for w in query.lower().split() if len(w) > 3]
        results: List[SearchResult] = []
        try:
            resp = http_session.get("https://www.arbeitnow.com/api/job-board-api", timeout=10)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for item in (resp.json().get("data", []) or []):
                title = item.get("title", "")
                hay = (title + " " + str(item.get("description", "")) + " " + " ".join(item.get("tags", []) or [])).lower()
                if terms and not any(t in hay for t in terms):
                    continue
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=title,
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source_name=item.get("company_name", "Arbeitnow"),
                    published_date=str(item.get("created_at", "")),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("Arbeitnow search failed: %s", e)
        return results


arbeitnow_provider = ArbeitnowProvider()
