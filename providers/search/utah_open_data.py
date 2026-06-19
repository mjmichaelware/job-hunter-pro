"""Utah Open Data (Socrata) — SLC business-license employer LEADS (not postings).
Keyless (optional UTAH_OPENDATA_APP_TOKEN raises rate limits). Default OFF: set
ENABLE_UTAH_OPENDATA=1 to include these employer leads in discovery.
Dataset: opendata.utah.gov SLC Business Licenses (hi6r-u5gn).
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

DATASET = os.environ.get("UTAH_OPENDATA_DATASET", "hi6r-u5gn")


class UtahOpenDataProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="utah_open_data",
            label="Utah Open Data (employer leads)",
            type=ProviderType.SEARCH,
            description="SLC business-license employers as opportunity leads (not job posts).",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return "" if os.environ.get("ENABLE_UTAH_OPENDATA") else "Set ENABLE_UTAH_OPENDATA=1 to include employer leads."

    def search(self, query: str) -> List[SearchResult]:
        params = {"$limit": 50}
        q = query.strip()
        if q:
            params["$q"] = q
        headers = {}
        tok = Config.provider_key("UTAH_OPENDATA_APP_TOKEN")
        if tok:
            headers["X-App-Token"] = tok
        results: List[SearchResult] = []
        try:
            url = "https://opendata.utah.gov/resource/%s.json" % DATASET
            resp = http_session.get(url, params=params, headers=headers, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for row in (resp.json() or []):
                name = row.get("business_name") or row.get("name") or row.get("dba_name") or ""
                if not name:
                    continue
                addr = row.get("address") or row.get("street_address") or row.get("location_address") or ""
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title="Employer lead: %s" % name,
                    url="https://opendata.utah.gov/resource/%s.json" % DATASET,
                    snippet=str(addr),
                    source_name=name,
                    published_date=None,
                    raw_json=row,
                    confidence=0.5,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("Utah Open Data failed: %s", e)
        return results


utah_open_data_provider = UtahOpenDataProvider()
