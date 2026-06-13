import logging
from typing import List
import requests
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider, ProviderStatus
from core import Config, http_session

logger = logging.getLogger(__name__)

class JoobleProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="jooble",
            label="Jooble",
            type=ProviderType.SEARCH,
            description="Worldwide job aggregator. Requires API Key.",
            supports_live_jobs=True,
        )

    def is_available(self) -> bool:
        return bool(Config.JOOBLE_API_KEY)

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls Jooble API: https://jooble.org/api/queries/v1/us
        """
        if not self.is_available():
            return []

        results = []
        try:
            url = f"https://jooble.org/api/queries/v1/us/{Config.JOOBLE_API_KEY}"
            payload = {
                "keywords": query,
                "location": "Salt Lake City, UT",
            }
            
            response = http_session.post(url, json=payload, timeout=Config.REQUEST_TIMEOUT)
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
                )
                results.append(res)
        except requests.exceptions.HTTPError as e:
            # This will be used for the quarantine logic later
            logger.error(f"Jooble search failed with HTTP error: {e.response.status_code}")
            # Re-raise the exception so the bridge can handle it
            raise e
        except Exception as e:
            logger.error(f"Jooble search failed with a general error: {e}")
            
        return results

jooble_provider = JoobleProvider()
