"""BambooHR ATS — keyless per-company JSON.

Sweeps curated Utah company slugs. Each slug's careers list is public.
Endpoint: https://{slug}.bamboohr.com/careers/list
Response JSON: { result: [ { title: {label}, location: {city, state}, department: {label} } ] }
"""
import logging
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

log = logging.getLogger(__name__)

# (slug, display_name, address)
_COMPANIES = [
    ("entrata", "Entrata", "2912 Executive Pkwy, Lehi UT"),
    ("podiumco", "Podium", "1350 W Traverse Pkwy, Lehi UT"),
    ("progrexion", "Progrexion", "257 W 200 S, Salt Lake City UT"),
    ("chatbooks", "Chatbooks", "75 W Center St, Provo UT"),
    ("canopytax", "Canopy", "2780 S. Jones Blvd, Las Vegas NV"),
    ("mxtechnologies", "MX Technologies", "3401 N Thanksgiving Way, Lehi UT"),
    ("kuali", "Kuali", "1905 N 100 W, Lehi UT"),
    ("instructure", "Instructure", "6330 S 3000 E, Salt Lake City UT"),
    ("downeastoutfitters", "DownEast Outfitters", "6951 S 300 W, Midvale UT"),
    ("simplecitizen", "SimpleCitizen", "SLC UT"),
]


class BambooHRProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="bamboohr",
            label="BambooHR Careers",
            type=ProviderType.SEARCH,
            description="Career listings from Utah companies using BambooHR ATS",
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
        for slug, company_name, address in _COMPANIES:
            try:
                url = "https://%s.bamboohr.com/careers/list" % slug
                resp = http_session.get(url, timeout=10)
                check_hard_failure(self.metadata.key, resp)
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                data = resp.json()
                items = data.get("result", []) if isinstance(data, dict) else []
                for item in items:
                    title_obj = item.get("title") or {}
                    title = title_obj.get("label", "") if isinstance(title_obj, dict) else str(title_obj)
                    dept_obj = item.get("department") or {}
                    dept = dept_obj.get("label", "") if isinstance(dept_obj, dict) else ""
                    loc_obj = item.get("location") or {}
                    city = loc_obj.get("city", "") if isinstance(loc_obj, dict) else ""
                    state = loc_obj.get("state", "") if isinstance(loc_obj, dict) else ""
                    loc_str = "%s, %s" % (city, state) if city else address
                    # Filter by query keyword
                    searchable = " ".join([title, dept, city, state]).lower()
                    if q_lower and q_lower not in searchable:
                        continue
                    job_id = item.get("id", "")
                    job_url = "https://%s.bamboohr.com/careers/%s" % (slug, job_id) if job_id else url
                    results.append(SearchResult(
                        provider=self.metadata.key,
                        query=query,
                        title=title,
                        url=job_url,
                        snippet="%s — %s" % (dept, loc_str) if dept else loc_str,
                        source_name=company_name,
                        published_date=None,
                        raw_json=item,
                        confidence=1.0,
                        cost_units=0.0,
                    ))
                    if len(results) >= limit:
                        return results
            except ProviderHardFailure:
                raise
            except Exception as e:
                log.error("BambooHR slug %s failed: %s", slug, e)
        return results


bamboohr_provider = BambooHRProvider()
