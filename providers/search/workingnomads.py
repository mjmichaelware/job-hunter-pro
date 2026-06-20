"""Working Nomads remote jobs — keyless JSON API.

Endpoint: https://www.workingnomads.com/api/exposed_jobs/?limit={limit}
Response: list of { title, company_name, url, category, pub_date, location, description }
"""
import logging
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

log = logging.getLogger(__name__)

_BASE_URL = "https://www.workingnomads.com/api/exposed_jobs/"


class WorkingNomadsProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="workingnomads",
            label="Working Nomads",
            type=ProviderType.SEARCH,
            description="Remote job listings for digital workers",
            requires_api_key=False,
            budget_class="free",
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return ""

    def search(self, query: str, location: str = "", limit: int = 50) -> List[SearchResult]:
        results: List[SearchResult] = []
        q_lower = query.lower().strip()
        try:
            params = {"limit": min(limit, 100)}
            resp = http_session.get(_BASE_URL, params=params, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            data = resp.json()
            items = data if isinstance(data, list) else data.get("results", [])
            for item in items:
                title = (item.get("title") or "").strip()
                category = (item.get("category") or "").strip()
                searchable = " ".join([title, category]).lower()
                if q_lower and q_lower not in searchable:
                    continue
                company = (item.get("company_name") or "").strip()
                url = (item.get("url") or "").strip()
                description = (item.get("description") or "")[:300]
                loc = (item.get("location") or "Remote").strip()
                pub_date = item.get("pub_date")
                if not title:
                    continue
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=title,
                    url=url,
                    snippet="%s — %s" % (loc, description) if description else loc,
                    source_name=company or "Working Nomads",
                    published_date=str(pub_date) if pub_date else None,
                    raw_json=item,
                    confidence=1.0,
                    cost_units=0.0,
                ))
                if len(results) >= limit:
                    break
        except ProviderHardFailure:
            raise
        except Exception as e:
            log.error("WorkingNomads search failed: %s", e)
        return results


workingnomads_provider = WorkingNomadsProvider()
