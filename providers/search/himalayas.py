"""Himalayas remote jobs API — keyless JSON. https://himalayas.app/jobs/api

Returns real remote job listings. No key required.
API: GET https://himalayas.app/jobs/api?limit=100&search=<query>
"""
import logging
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

_BASE_URL = "https://himalayas.app/jobs/api"


class HimalayasProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="himalayas",
            label="Himalayas",
            type=ProviderType.SEARCH,
            description="Keyless remote-jobs API with search support.",
            requires_api_key=False,
            budget_class="free",
        )

    def is_available(self) -> bool:
        return True

    def search(self, query: str) -> List[SearchResult]:
        results: List[SearchResult] = []
        try:
            params = {"limit": 50}
            q = query.strip()
            if q:
                params["search"] = q
            resp = http_session.get(_BASE_URL, params=params, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            data = resp.json()
            jobs = data if isinstance(data, list) else data.get("jobs", []) or []
            for item in jobs:
                title = item.get("title", "") or item.get("jobTitle", "")
                company = (item.get("company") or {}).get("name", "") if isinstance(item.get("company"), dict) else item.get("companyName", "")
                url = item.get("url", "") or item.get("applicationUrl", "")
                snippet = item.get("description", "") or item.get("shortDescription", "")
                location = item.get("location", "") or "Remote"
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=title,
                    url=url,
                    snippet="%s — %s" % (location, snippet[:200]) if snippet else location,
                    source_name=company or "Himalayas",
                    published_date=item.get("publishedAt") or item.get("createdAt"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("Himalayas search failed: %s", e)
        return results


himalayas_provider = HimalayasProvider()
