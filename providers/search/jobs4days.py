"""4 Day Week — keyless career source.\n\nJobs offering a 4-day work week"""
import logging
from typing import List
from urllib.parse import quote_plus

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

log = logging.getLogger(__name__)


class FourDayWeekProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="jobs4days",
            label="4 Day Week",
            type=ProviderType.SEARCH,
            description="Jobs offering a 4-day work week",
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
            url = "https://4dayweek.io/api/job-board/public-jobs?search=%s" % quote_plus(query.strip())
            resp = http_session.get(url, timeout=12, headers={"Accept": "application/json"})
            check_hard_failure(self.metadata.key, resp)
            if resp.status_code == 404:
                return results
            resp.raise_for_status()
            data = resp.json()
            items = data.get("jobs", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            ql = query.lower().strip()
            for it in items[:limit]:
                title = str(it.get("title") or it.get("position") or "" if isinstance(it, dict) else it)
                if not title:
                    continue
                hay = " ".join(str(x) for x in [it.get("title",""), it.get("company_name",""), it.get("location","")]).lower()
                if ql and ql not in hay:
                    continue
                results.append(SearchResult(
                    provider=self.metadata.key, query=query, title=title,
                    url=str(it.get("url") or it.get("apply_url") or "" if isinstance(it, dict) else "") or url,
                    snippet=(str(it.get("company_name","") if isinstance(it, dict) else "")[:300] or None),
                    source_name=it.get("company_name") or "4 Day Week" if isinstance(it, dict) else "4 Day Week", published_date=it.get("published_at") if isinstance(it, dict) else None,
                    raw_json=it if isinstance(it, dict) else {"v": it},
                    confidence=1.0, cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            log.error("4 Day Week search failed: %s", e)
        return results


jobs4days_provider = FourDayWeekProvider()
