import logging
from typing import List
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider
from core import http_session

logger = logging.getLogger(__name__)

class TheMuseProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="themuse",
            label="The Muse",
            type=ProviderType.SEARCH,
            description="Job board with a focus on company culture. Keyless access.",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True # Does not require an API key

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls The Muse public API: https://www.themuse.com/api/public/jobs
        """
        results = []
        try:
            # The Muse uses 'category', 'location', 'level' but also has a general 'page'
            # For a general search, we can use their params. 
            # Note: The Muse doesn't have a direct 'q=' query param that searches everything,
            # but we can try to pass it as a category or just get latest.
            # To match the generic 'query' from our federated search, we'll try to find matches.
            url = "https://www.themuse.com/api/public/jobs"
            params = {
                "page": 0,
                # "location": "Salt Lake City, UT" # We could seed this from config if needed
            }
            
            response = http_session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            items = data.get("results", [])
            for item in items:
                title = item.get("name", "")
                # Simple keyword filter since The Muse API doesn't have a broad 'q' param
                if query.lower() not in title.lower() and query.lower() not in item.get("contents", "").lower():
                    continue

                res = SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=title,
                    url=item.get("refs", {}).get("landing_page", ""),
                    snippet=item.get("contents", ""),
                    source_name=item.get("company", {}).get("name", "The Muse"),
                    published_date=item.get("publication_date"),
                    raw_json=item, # Note: original model had raw_json, not raw_payload
                    confidence=1.0,
                    cost_units=0.0
                )
                results.append(res)
                
        except Exception as e:
            logger.error(f"The Muse search failed: {e}")
            
        return results

themuse_provider = TheMuseProvider()
