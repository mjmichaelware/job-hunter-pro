"""Jobicy — keyless remote-jobs API v2. https://jobicy.com/api/v2/remote-jobs"""
import logging
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)


class JobicyProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="jobicy",
            label="Jobicy",
            type=ProviderType.SEARCH,
            description="Keyless remote-jobs API (geo + tag params).",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def search(self, query: str) -> List[SearchResult]:
        params = {"count": 50}
        tag = " ".join([w for w in query.split() if len(w) > 2])
        if tag:
            params["tag"] = tag
        results: List[SearchResult] = []
        try:
            resp = http_session.get("https://jobicy.com/api/v2/remote-jobs", params=params, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for item in (resp.json().get("jobs", []) or []):
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=item.get("jobTitle", ""),
                    url=item.get("url", ""),
                    snippet=item.get("jobExcerpt", ""),
                    source_name=item.get("companyName", "Jobicy"),
                    published_date=item.get("pubDate"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("Jobicy search failed: %s", e)
        return results


jobicy_provider = JobicyProvider()
