import logging
from typing import List
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider
from core import Config, http_session

logger = logging.getLogger(__name__)

class AdzunaProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="adzuna",
            label="Adzuna",
            type=ProviderType.SEARCH,
            description="Job search provider Adzuna. Requires App ID and Key.",
        )

    def is_available(self) -> bool:
        return bool(Config.ADZUNA_APP_ID and Config.ADZUNA_APP_KEY)

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls Adzuna API: https://api.adzuna.com/v1/api/jobs/us/search/1
        """
        if not self.is_available():
            return list()

        results = []
        try:
            # Example: https://api.adzuna.com/v1/api/jobs/us/search/1?app_id={id}&app_key={key}&what=cook&where=Salt%20Lake%20City
            url = f"https://api.adzuna.com/v1/api/jobs/us/search/1"
            params = {
                "app_id": Config.ADZUNA_APP_ID,
                "app_key": Config.ADZUNA_APP_KEY,
                "what": query,
                "content-type": "application/json"
            }
            
            response = http_session.get(url, params=params, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            items = data.get("results", [])
            for item in items:
                res = SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=item.get("title", ""),
                    url=item.get("redirect_url", ""),
                    snippet=item.get("description", ""),
                    source_name=item.get("company", {}).get("display_name"),
                    published_date=item.get("created"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=1.0
                )
                results.append(res)
                
        except Exception as e:
            logger.error(f"Adzuna search failed: {e}")
            
        return results

adzuna_provider = AdzunaProvider()
