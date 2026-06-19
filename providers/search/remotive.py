"""Remotive — keyless remote-jobs API. https://remotive.com/api/remote-jobs"""
import logging
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)


class RemotiveProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="remotive",
            label="Remotive",
            type=ProviderType.SEARCH,
            description="Keyless remote-jobs API (search param supported).",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def search(self, query: str) -> List[SearchResult]:
        params = {"limit": 50}
        q = " ".join([w for w in query.split() if len(w) > 2])
        if q:
            params["search"] = q
        results: List[SearchResult] = []
        try:
            resp = http_session.get("https://remotive.com/api/remote-jobs", params=params, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for item in (resp.json().get("jobs", []) or []):
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source_name=item.get("company_name", "Remotive"),
                    published_date=item.get("publication_date"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("Remotive search failed: %s", e)
        return results


remotive_provider = RemotiveProvider()
