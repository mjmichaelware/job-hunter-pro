"""Foursquare Places — local businesses near 84115 as opportunity LEADS.
Keyed (free tier): FOURSQUARE_API_KEY. Default OFF: set ENABLE_FOURSQUARE=1.
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

FSQ_NEAR = os.environ.get("FOURSQUARE_NEAR", "Salt Lake City, UT 84115")


class FoursquareProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="foursquare",
            label="Foursquare Places (business leads)",
            type=ProviderType.SEARCH,
            description="Local businesses near 84115 as leads. Free key.",
            requires_api_key=True,
        )

    def is_available(self) -> bool:
        return bool(Config.provider_key("FOURSQUARE_API_KEY"))

    def disabled_reason(self) -> str:
        return "" if os.environ.get("ENABLE_FOURSQUARE") else "Set ENABLE_FOURSQUARE=1 to include business leads."

    def search(self, query: str) -> List[SearchResult]:
        key = Config.provider_key("FOURSQUARE_API_KEY")
        if not key:
            return []
        params = {"near": FSQ_NEAR, "limit": 50}
        if query.strip():
            params["query"] = query.strip()
        results: List[SearchResult] = []
        try:
            resp = http_session.get(
                "https://api.foursquare.com/v3/places/search",
                params=params, headers={"Authorization": key, "accept": "application/json"}, timeout=12,
            )
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for place in (resp.json().get("results", []) or []):
                name = place.get("name", "")
                loc = (place.get("location", {}) or {}).get("formatted_address", "")
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title="Business lead: %s" % name,
                    url="https://foursquare.com/v/%s" % place.get("fsq_id", ""),
                    snippet=str(loc),
                    source_name=name,
                    published_date=None,
                    raw_json=place,
                    confidence=0.5,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("Foursquare failed: %s", e)
        return results


foursquare_provider = FoursquareProvider()
