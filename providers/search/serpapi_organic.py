import logging
import os
from typing import List, Dict
from models import SearchResult
from ..base import Provider, ProviderMetadata, ProviderType, SearchProvider
from core import Config, http_session

logger = logging.getLogger(__name__)

def _enabled() -> bool:
    return str(os.environ.get("ENABLE_SERPAPI_ORGANIC", "")).strip() in {"1", "true", "True", "yes", "on"}

class SerpApiOrganicProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="serpapi_organic",
            label="SerpAPI (Google Organic)",
            type=ProviderType.SEARCH,
            description="Organic web search via SerpAPI. OFF by default to protect quota; set ENABLE_SERPAPI_ORGANIC=1.",
        )

    def disabled_reason(self) -> str:
        # Organic search is not primary job discovery and burns scarce SerpAPI
        # quota, so it is off unless explicitly enabled.
        return "" if _enabled() else "off_by_default (ENABLE_SERPAPI_ORGANIC=1 to enable)"

    def is_available(self) -> bool:
        return _enabled() and bool(Config.SERPAPI_KEY)

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls SerpAPI organic Google search.
        """
        if not self.is_available():
            logger.warning(f"{self.metadata.label} key missing or disabled.")
            return list()

        from ._serpapi_budget import allows_search
        if not allows_search():
            logger.warning("SerpAPI budget guard active; skipping SerpAPI organic search.")
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
                
        except Exception as e:
            logger.error(f"SerpAPI Organic search failed: {e}")
            
        return results

serpapi_organic_provider = SerpApiOrganicProvider()
