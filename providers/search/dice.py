"""Dice technology jobs — public search API (graceful degradation).

Primary: https://job-search-api.solutiondevelopers.com/v2/positions/search?q={query}&location=...
Fallback: https://www.dice.com/api/1.0/seeker/jobsearch/V1?q={query}&l=Salt+Lake+City%2C+UT&num_rec=25
Returns [] on any failure.
"""
import logging
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

log = logging.getLogger(__name__)

_PRIMARY_URL = "https://job-search-api.solutiondevelopers.com/v2/positions/search"
_FALLBACK_URL = "https://www.dice.com/api/1.0/seeker/jobsearch/V1"


class DiceProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="dice",
            label="Dice",
            type=ProviderType.SEARCH,
            description="Technology and professional jobs in Utah",
            requires_api_key=False,
            budget_class="free",
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return ""

    def _parse_items(self, data: object, query: str) -> List[SearchResult]:
        results: List[SearchResult] = []
        items: list = []
        if isinstance(data, dict):
            items = (data.get("data") or data.get("resultItemList") or
                     data.get("jobs") or data.get("results") or [])
        elif isinstance(data, list):
            items = data
        for item in items:
            title = (item.get("title") or item.get("jobTitle") or "").strip()
            url = (item.get("url") or item.get("applyUrl") or item.get("detailUrl") or "").strip()
            company = (item.get("company") or item.get("companyName") or "").strip()
            loc = (item.get("location") or item.get("locationDescription") or "Salt Lake City, UT").strip()
            if not title:
                continue
            results.append(SearchResult(
                provider=self.metadata.key,
                query=query,
                title=title,
                url=url,
                snippet=loc,
                source_name=company or "Dice",
                published_date=item.get("postedDate") or item.get("date"),
                raw_json=item,
                confidence=1.0,
                cost_units=0.0,
            ))
        return results

    def search(self, query: str, location: str = "", limit: int = 50) -> List[SearchResult]:
        results: List[SearchResult] = []
        loc = location.strip() or "Salt Lake City, UT"
        try:
            params = {"q": query.strip(), "location": loc, "radius": 25, "limit": min(limit, 50)}
            resp = http_session.get(_PRIMARY_URL, params=params, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            results = self._parse_items(resp.json(), query)
            if results:
                return results
        except ProviderHardFailure:
            raise
        except Exception as e:
            log.warning("Dice primary endpoint failed: %s — trying fallback", e)
        try:
            params2 = {"q": query.strip(), "l": loc, "num_rec": min(limit, 25)}
            resp2 = http_session.get(_FALLBACK_URL, params=params2, timeout=12)
            check_hard_failure(self.metadata.key, resp2)
            resp2.raise_for_status()
            results = self._parse_items(resp2.json(), query)
        except ProviderHardFailure:
            raise
        except Exception as e2:
            log.error("Dice fallback endpoint failed: %s", e2)
        return results


dice_provider = DiceProvider()
