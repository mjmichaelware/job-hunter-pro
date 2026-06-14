import logging
from typing import List
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure
from core import Config, http_session
from core.errors import ProviderHardFailure
from services.provider_status import is_policy_disabled

logger = logging.getLogger(__name__)

class JoobleProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="jooble",
            label="Jooble",
            type=ProviderType.SEARCH,
            description="Worldwide job aggregator. Disabled by default (compromised/unreliable upstream; set ENABLE_JOOBLE=1).",
        )

    def is_available(self) -> bool:
        # Disabled by default: repeated 403s upstream and credentials treated as
        # compromised. Re-enable only via ENABLE_JOOBLE=1.
        if is_policy_disabled(self.metadata.key):
            return False
        return bool(Config.JOOBLE_API_KEY)

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls Jooble API: https://jooble.org/api/queries/v1/us
        """
        if not self.is_available():
            return list()

        results = []
        try:
            url = f"https://jooble.org/api/queries/v1/us/{Config.JOOBLE_API_KEY}"
            # Jooble uses POST with JSON body
            payload = {
                "keywords": query,
                "location": "Salt Lake City, UT",
            }
            
            response = http_session.post(url, json=payload, timeout=Config.REQUEST_TIMEOUT)
            check_hard_failure(self.metadata.key, response)
            response.raise_for_status()
            data = response.json()
            
            jobs = data.get("jobs", [])
            for item in jobs:
                res = SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source_name=item.get("company", "Jooble"),
                    published_date=item.get("updated"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=1.0
                )
                results.append(res)

        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error(f"Jooble search failed: {e}")

        return results

jooble_provider = JoobleProvider()
