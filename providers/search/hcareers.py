"""HCareers — keyless career source.\n\nHotel, restaurant, and hospitality job board"""
import logging
from typing import List
from urllib.parse import quote_plus

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

log = logging.getLogger(__name__)


class HCareersProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="hcareers",
            label="HCareers",
            type=ProviderType.SEARCH,
            description="Hotel, restaurant, and hospitality job board",
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
            url = "https://www.hcareers.com/api/JobSearch?q=%s&l=Salt+Lake+City%%2C+UT&range=25" % quote_plus(query.strip())
            resp = http_session.get(url, timeout=12, headers={"Accept": "application/json"})
            check_hard_failure(self.metadata.key, resp)
            if resp.status_code == 404:
                return results
            resp.raise_for_status()
            data = resp.json()
            items = data.get("results", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            ql = query.lower().strip()
            for it in items[:limit]:
                title = str(it.get("title") or it.get("jobTitle") or "" if isinstance(it, dict) else it)
                if not title:
                    continue
                hay = " ".join(str(x) for x in [it.get("title",""), it.get("company",""), it.get("location","")]).lower()
                if ql and ql not in hay:
                    continue
                results.append(SearchResult(
                    provider=self.metadata.key, query=query, title=title,
                    url=str(it.get("url") or it.get("jobUrl") or "" if isinstance(it, dict) else "") or url,
                    snippet=(str(it.get("company","") if isinstance(it, dict) else "")[:300] or None),
                    source_name=it.get("company") or "HCareers" if isinstance(it, dict) else "HCareers", published_date=it.get("datePosted") if isinstance(it, dict) else None,
                    raw_json=it if isinstance(it, dict) else {"v": it},
                    confidence=1.0, cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            log.error("HCareers search failed: %s", e)
        return results


hcareers_provider = HCareersProvider()
