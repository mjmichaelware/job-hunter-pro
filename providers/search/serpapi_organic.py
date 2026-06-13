import logging
from typing import List, Dict
import requests
from models import SearchResult
from ..base import Provider, ProviderMetadata, ProviderType, SearchProvider, ProviderStatus
from core import Config, http_session

logger = logging.getLogger(__name__)

class SerpApiOrganicProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="serpapi_organic",
            label="SerpAPI (Google Organic)",
            type=ProviderType.SEARCH,
            description="Performs organic web searches via SerpAPI. Budget-gated.",
            supports_live_jobs=True,
        )

    def is_available(self) -> bool:
        return bool(Config.SERPAPI_KEY)

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls SerpAPI organic Google search.
        """
        if not self.is_available():
            logger.warning(f"{self.metadata.label} key missing.")
            return list()

        results = []
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": Config.SERPAPI_KEY,
                "engine": "google",
                "hl": "en",
            }
            
            response = http_session.get(url, params=params, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            organic_results = data.get("organic_results", [])
            for item in organic_results:
                title = item.get("title", "")
                link = item.get("link", "")
                snippet = item.get("snippet", "")
                
                res = SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=title,
                    url=link,
                    snippet=snippet,
                    source_name=item.get("displayed_link"),
                    raw_json=item,
                    confidence=0.8, # Organic is lower confidence for actual job posts
                    cost_units=1.0
                )
                results.append(res)
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"SerpAPI Organic search failed with HTTP error: {e.response.status_code}")
            raise e
        except Exception as e:
            logger.error(f"SerpAPI Organic search failed: {e}")
            
        return results

serpapi_organic_provider = SerpApiOrganicProvider()
