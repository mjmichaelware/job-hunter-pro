"""CareerOneStop (US DOL) Job Search API — real postings near a ZIP+radius.
Keyed (free): CAREERONESTOP_USERID + CAREERONESTOP_TOKEN (one free signup).
Docs: https://www.careeronestop.org/Developers/WebAPI/web-api.aspx
"""
import logging
import os
from urllib.parse import quote
from typing import List

from models import SearchResult
from core import http_session
from core.config import Config
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

COS_LOCATION = os.environ.get("CAREERONESTOP_LOCATION", "84115")
COS_RADIUS = os.environ.get("CAREERONESTOP_RADIUS", "50")


class CareerOneStopProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="careeronestop",
            label="CareerOneStop (US DOL)",
            type=ProviderType.SEARCH,
            description="Government job search near a ZIP+radius. Free key (userId+token).",
            requires_api_key=True,
        )

    def is_available(self) -> bool:
        return bool(Config.provider_key("CAREERONESTOP_USERID") and Config.provider_key("CAREERONESTOP_TOKEN"))

    def search(self, query: str) -> List[SearchResult]:
        user = Config.provider_key("CAREERONESTOP_USERID")
        token = Config.provider_key("CAREERONESTOP_TOKEN")
        if not (user and token):
            return []
        kw = quote(query.strip() or "jobs", safe="")
        url = "https://api.careeronestop.org/v1/jobsearch/%s/%s/%s/%s/jobdate/desc/0/50/30" % (
            user, kw, quote(COS_LOCATION, safe=""), COS_RADIUS,
        )
        results: List[SearchResult] = []
        try:
            resp = http_session.get(url, headers={"Authorization": "Bearer %s" % token}, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for item in (resp.json().get("Jobs", []) or []):
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=item.get("JobTitle", ""),
                    url=item.get("URL", ""),
                    snippet=item.get("Location", ""),
                    source_name=item.get("Company", "CareerOneStop"),
                    published_date=item.get("AccquisitionDate") or item.get("AcquisitionDate"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("CareerOneStop search failed: %s", e)
        return results


careeronestop_provider = CareerOneStopProvider()
