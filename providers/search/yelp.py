"""Yelp Fusion — local businesses + ratings near 84115 as opportunity LEADS
(also feeds future Core Rating). Keyed (free tier): YELP_API_KEY.
Default OFF: set ENABLE_YELP=1 to include in discovery.
"""
import logging
import os
from typing import List

from models import SearchResult
from core import http_session
from core.config import Config
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

YELP_LOCATION = os.environ.get("YELP_LOCATION", "84115")
YELP_RADIUS_M = int(os.environ.get("YELP_RADIUS_M", "40000"))  # Yelp max 40000m


class YelpProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="yelp",
            label="Yelp Fusion (business leads)",
            type=ProviderType.SEARCH,
            description="Local businesses + ratings near 84115 as leads. Free key.",
            requires_api_key=True,
        )

    def is_available(self) -> bool:
        return bool(Config.provider_key("YELP_API_KEY"))

    def disabled_reason(self) -> str:
        return "" if os.environ.get("ENABLE_YELP") else "Set ENABLE_YELP=1 to include business leads."

    def search(self, query: str) -> List[SearchResult]:
        key = Config.provider_key("YELP_API_KEY")
        if not key:
            return []
        params = {"location": YELP_LOCATION, "radius": YELP_RADIUS_M, "limit": 50}
        if query.strip():
            params["term"] = query.strip()
        results: List[SearchResult] = []
        try:
            resp = http_session.get(
                "https://api.yelp.com/v3/businesses/search",
                params=params, headers={"Authorization": "Bearer %s" % key}, timeout=12,
            )
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for biz in (resp.json().get("businesses", []) or []):
                name = biz.get("name", "")
                loc = ", ".join((biz.get("location", {}) or {}).get("display_address", []) or [])
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title="Business lead: %s" % name,
                    url=biz.get("url", ""),
                    snippet="%s · %s★ (%s reviews)" % (loc, biz.get("rating", "?"), biz.get("review_count", "?")),
                    source_name=name,
                    published_date=None,
                    raw_json=biz,
                    confidence=0.5,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("Yelp failed: %s", e)
        return results


yelp_provider = YelpProvider()
