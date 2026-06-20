"""Snagajob hourly/part-time jobs — keyless public API (graceful degradation).

Endpoint: https://www.snagajob.com/api/v1/jobs?keyword={query}&location=Salt+Lake+City%2C+UT&radius=10&pagesize={limit}
Returns [] on any failure (auth may be required).
"""
import logging
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

log = logging.getLogger(__name__)

_BASE_URL = "https://www.snagajob.com/api/v1/jobs"


class SnagajobProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="snagajob",
            label="Snagajob",
            type=ProviderType.SEARCH,
            description="Hourly and part-time jobs near Salt Lake City",
            requires_api_key=False,
            budget_class="free",
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return ""

    def search(self, query: str, location: str = "", limit: int = 50) -> List[SearchResult]:
        results: List[SearchResult] = []
        try:
            params = {
                "keyword": query.strip(),
                "location": location.strip() or "Salt Lake City, UT",
                "radius": 10,
                "pagesize": min(limit, 50),
            }
            resp = http_session.get(_BASE_URL, params=params, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            data = resp.json()
            items = (data.get("jobs") or data.get("results") or
                     data.get("data") or []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for item in items[:limit]:
                title = (item.get("title") or item.get("jobTitle") or "").strip()
                url = (item.get("url") or item.get("jobUrl") or item.get("applyUrl") or "").strip()
                company = (item.get("employer") or item.get("companyName") or item.get("company") or "").strip()
                loc = (item.get("location") or item.get("city") or "Salt Lake City, UT").strip()
                if isinstance(company, dict):
                    company = company.get("name", "")
                if not title:
                    continue
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=title,
                    url=url,
                    snippet=loc,
                    source_name=company or "Snagajob",
                    published_date=item.get("datePosted") or item.get("postedAt"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            log.error("Snagajob search failed: %s", e)
        return results


snagajob_provider = SnagajobProvider()
