"""SmartRecruiters public postings API — keyless per-company JSON.
Sweeps a configurable list of company identifiers (SMARTRECRUITERS_COMPANIES env overrides).
Default: curated list of employers known to use SmartRecruiters, including
national employers with Utah/SLC presence and remote-friendly companies.
Endpoint: https://api.smartrecruiters.com/v1/companies/{company}/postings
"""
import logging
import os
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

# Curated SmartRecruiters company identifiers.
# These are used directly in the API path. Override via SMARTRECRUITERS_COMPANIES env var.
_DEFAULT_SR_COMPANIES = [
    "IKEA",             # large national/international retailer with SLC store
    "Lidl",             # national grocery retailer expanding in US
    "Bosch",            # national employer with US manufacturing and service roles
    "Sephora",          # national retail, SLC-area stores
    "Panasonic",        # national employer with US presence
    "Electrolux",       # national appliance manufacturer with US roles
    "HiltonWorldwide",  # major hospitality employer, many SLC-area hotels
    "Compass",          # large food services / hospitality management company
    "Sodexo",           # food services / facilities, large SLC-area employer
    "Aramark",          # food services / hospitality, large national employer
]

_env_override = os.environ.get("SMARTRECRUITERS_COMPANIES", "")
SR_COMPANIES = [s.strip() for s in _env_override.split(",") if s.strip()] if _env_override else _DEFAULT_SR_COMPANIES


class SmartRecruitersProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="smartrecruiters",
            label="SmartRecruiters (ATS boards)",
            type=ProviderType.SEARCH,
            description="Keyless public ATS postings; sweeps curated employers (override via SMARTRECRUITERS_COMPANIES).",
            requires_api_key=False,
            budget_class="free",
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return "" if SR_COMPANIES else "SMARTRECRUITERS_COMPANIES list is empty; set SMARTRECRUITERS_COMPANIES=co1,co2."

    def search(self, query: str) -> List[SearchResult]:
        terms = [w for w in query.lower().split() if len(w) > 3]
        results: List[SearchResult] = []
        for company in SR_COMPANIES:
            try:
                url = "https://api.smartrecruiters.com/v1/companies/%s/postings" % company
                resp = http_session.get(
                    url,
                    params={"limit": 50},
                    headers={"Accept": "application/json"},
                    timeout=12,
                )
                check_hard_failure(self.metadata.key, resp)
                if resp.status_code == 404:
                    logger.debug("SmartRecruiters company not found: %s", company)
                    continue
                resp.raise_for_status()
                for item in (resp.json().get("content", []) or []):
                    title = item.get("name", "")
                    if terms and not any(t in title.lower() for t in terms):
                        continue
                    loc = (item.get("location") or {})
                    loc_str = ", ".join(filter(None, [
                        loc.get("city", ""),
                        loc.get("region", ""),
                        loc.get("country", ""),
                    ]))
                    ref_num = item.get("refNumber", "")
                    job_url = "https://jobs.smartrecruiters.com/%s/%s" % (company, ref_num) if ref_num else ""
                    results.append(SearchResult(
                        provider=self.metadata.key,
                        query=query,
                        title=title,
                        url=job_url,
                        snippet=loc_str or item.get("department", {}).get("label", ""),
                        source_name=company,
                        published_date=item.get("releasedDate") or item.get("updatedOn"),
                        raw_json=item,
                        confidence=1.0,
                        cost_units=0.0,
                    ))
            except ProviderHardFailure:
                raise
            except Exception as e:
                logger.error("SmartRecruiters company %s failed: %s", company, e)
        return results


smartrecruiters_provider = SmartRecruitersProvider()
