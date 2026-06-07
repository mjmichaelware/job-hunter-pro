import logging
from typing import List
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider
from core import Config, http_session

logger = logging.getLogger(__name__)

class CareerjetProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="careerjet",
            label="Careerjet",
            type=ProviderType.SEARCH,
            description="International job search engine. Requires Affiliate ID.",
        )

    def is_available(self) -> bool:
        return bool(Config.CAREERJET_AFFID)

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls Careerjet API: http://public.api.careerjet.net/search
        """
        if not self.is_available():
            return list()

        results = []
        try:
            url = "http://public.api.careerjet.net/search"
            # Careerjet requires user_ip and user_agent
            params = {
                "affid": Config.CAREERJET_AFFID,
                "keywords": query,
                "location": "Salt Lake City, UT",
                "user_ip": "127.0.0.1",
                "user_agent": "JobHunterPro/1.0"
            }
            
            response = http_session.get(url, params=params, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            jobs = data.get("jobs", [])
            for item in jobs:
                res = SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source_name=item.get("company", "Careerjet"),
                    published_date=item.get("date"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=1.0
                )
                results.append(res)
                
        except Exception as e:
            logger.error(f"Careerjet search failed: {e}")
            
        return results

careerjet_provider = CareerjetProvider()
