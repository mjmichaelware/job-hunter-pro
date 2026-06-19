"""USAspending.gov — federal award recipients in Utah as contractor/employer LEADS
(not job posts). Keyless. Default OFF: set ENABLE_USASPENDING=1 to include.
"""
import logging
import os
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

STATE = os.environ.get("USASPENDING_STATE", "UT")


class USASpendingProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="usaspending",
            label="USAspending (contractor leads)",
            type=ProviderType.SEARCH,
            description="Recent federal award recipients in Utah as employer leads.",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return "" if os.environ.get("ENABLE_USASPENDING") else "Set ENABLE_USASPENDING=1 to include contractor leads."

    def search(self, query: str) -> List[SearchResult]:
        body = {
            "filters": {
                "award_type_codes": ["A", "B", "C", "D"],
                "place_of_performance_locations": [{"country": "USA", "state": STATE}],
            },
            "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency"],
            "page": 1, "limit": 50, "sort": "Award Amount", "order": "desc",
        }
        results: List[SearchResult] = []
        try:
            resp = http_session.post(
                "https://api.usaspending.gov/api/v2/search/spending_by_award/",
                json=body, timeout=15,
            )
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for row in (resp.json().get("results", []) or []):
                name = row.get("Recipient Name") or ""
                if not name:
                    continue
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title="Contractor lead: %s" % name,
                    url="https://www.usaspending.gov/search",
                    snippet="%s · %s" % (row.get("Awarding Agency", ""), row.get("Award Amount", "")),
                    source_name=name,
                    published_date=None,
                    raw_json=row,
                    confidence=0.4,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("USAspending failed: %s", e)
        return results


usaspending_provider = USASpendingProvider()
