"""Jobvite ATS — keyless per-company JSON.

Sweeps curated company slugs whose Jobvite career feeds are public.
Endpoint: https://jobs.jobvite.com/api/jobs?companyId={slug}
Response JSON: { requisitions: [ { title, briefDescription, locationName, applyLink } ] }
"""
import logging
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

log = logging.getLogger(__name__)

# (slug, display_name)
_COMPANIES = [
    ("marriott", "Marriott Hotels"),
    ("hilton", "Hilton"),
    ("ihg", "IHG Hotels"),
    ("hyatt", "Hyatt"),
    ("dollargeneral", "Dollar General"),
    ("ross", "Ross Stores"),
    ("tjx", "TJX Companies"),
    ("darden", "Darden Restaurants"),
    ("yum", "Yum! Brands"),
    ("compass", "Compass Group"),
]


class JobviteProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="jobvite",
            label="Jobvite Careers",
            type=ProviderType.SEARCH,
            description="Career listings from companies using the Jobvite ATS",
            requires_api_key=False,
            budget_class="free",
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return ""

    def search(self, query: str, location: str = "", limit: int = 50) -> List[SearchResult]:
        results: List[SearchResult] = []
        ql = query.lower().strip()
        for slug, company_name in _COMPANIES:
            try:
                url = "https://jobs.jobvite.com/api/jobs?companyId=%s" % slug
                resp = http_session.get(url, timeout=10, headers={"Accept": "application/json"})
                check_hard_failure(self.metadata.key, resp)
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                data = resp.json()
                reqs = data.get("requisitions", []) if isinstance(data, dict) else []
                for it in reqs:
                    if not isinstance(it, dict):
                        continue
                    title = str(it.get("title") or "")
                    if not title:
                        continue
                    loc = str(it.get("locationName") or "")
                    hay = " ".join([title, loc, str(it.get("briefDescription") or "")]).lower()
                    if ql and ql not in hay:
                        continue
                    results.append(SearchResult(
                        provider=self.metadata.key,
                        query=query,
                        title=title,
                        url=str(it.get("applyLink") or "") or url,
                        snippet=(str(it.get("briefDescription") or "")[:300] or loc or None),
                        source_name=company_name,
                        published_date=it.get("date") or None,
                        raw_json=it,
                        confidence=1.0,
                        cost_units=0.0,
                    ))
                    if len(results) >= limit:
                        return results
            except ProviderHardFailure:
                raise
            except Exception as e:
                log.error("Jobvite slug %s failed: %s", slug, e)
        return results


jobvite_provider = JobviteProvider()
