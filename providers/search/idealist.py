"""Idealist nonprofit/social-good jobs — keyless JSON API.

Endpoint: https://www.idealist.org/api/v4/listings?type=JOB&q={query}&location=Salt+Lake+City&radius=40&limit={limit}
Response JSON: { results: [ { name, organization: { name }, locations: [{ city }], url } ] }
"""
import logging
from typing import List
from urllib.parse import quote_plus

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

log = logging.getLogger(__name__)

_BASE_URL = "https://www.idealist.org/api/v4/listings"


class IdealistProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="idealist",
            label="Idealist",
            type=ProviderType.SEARCH,
            description="Nonprofit, social-service, and mission-driven jobs",
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
                "type": "JOB",
                "q": query.strip(),
                "location": location.strip() or "Salt Lake City",
                "radius": 40,
                "limit": min(limit, 50),
            }
            resp = http_session.get(_BASE_URL, params=params, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("results", []) if isinstance(data, dict) else []
            for item in items:
                title = (item.get("name") or "").strip()
                org = item.get("organization") or {}
                company = org.get("name", "") if isinstance(org, dict) else ""
                locations = item.get("locations") or []
                city = locations[0].get("city", "") if locations else ""
                url = (item.get("url") or "").strip()
                if not title:
                    continue
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=title,
                    url=url,
                    snippet=city or None,
                    source_name=company or "Idealist",
                    published_date=None,
                    raw_json=item,
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            log.error("Idealist search failed: %s", e)
        return results


idealist_provider = IdealistProvider()
