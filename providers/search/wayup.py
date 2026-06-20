"""WayUp — keyless career source.\n\nEntry-level, internship, and early-career jobs"""
import logging
from typing import List
from urllib.parse import quote_plus

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

log = logging.getLogger(__name__)


class WayUpProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="wayup",
            label="WayUp",
            type=ProviderType.SEARCH,
            description="Entry-level, internship, and early-career jobs",
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
            url = "https://www.wayup.com/listing-api/search/?q=%s&location=Salt+Lake+City%%2C+UT" % quote_plus(query.strip())
            resp = http_session.get(url, timeout=12, headers={"Accept": "application/json"})
            check_hard_failure(self.metadata.key, resp)
            if resp.status_code == 404:
                return results
            resp.raise_for_status()
            data = resp.json()
            items = data.get("results", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            ql = query.lower().strip()
            for it in items[:limit]:
                title = str(it.get("name") or it.get("title") or "" if isinstance(it, dict) else it)
                if not title:
                    continue
                hay = " ".join(str(x) for x in [it.get("name",""), it.get("employer_name",""), it.get("location","")]).lower()
                if ql and ql not in hay:
                    continue
                results.append(SearchResult(
                    provider=self.metadata.key, query=query, title=title,
                    url=str(it.get("url") or it.get("apply_url") or "" if isinstance(it, dict) else "") or url,
                    snippet=(str(it.get("employer_name","") if isinstance(it, dict) else "")[:300] or None),
                    source_name=it.get("employer_name") or "WayUp" if isinstance(it, dict) else "WayUp", published_date=it.get("created_at") if isinstance(it, dict) else None,
                    raw_json=it if isinstance(it, dict) else {"v": it},
                    confidence=1.0, cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            log.error("WayUp search failed: %s", e)
        return results


wayup_provider = WayUpProvider()
