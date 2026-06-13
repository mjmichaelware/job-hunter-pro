import logging
from typing import List
import requests
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider, ProviderStatus
from core import Config, http_session

logger = logging.getLogger(__name__)

class UsajobsProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="usajobs",
            label="USAJobs",
            type=ProviderType.SEARCH,
            description="Job search for US federal government positions. Requires API Key and Email.",
            supports_live_jobs=True,
        )

    def is_available(self) -> bool:
        return bool(Config.USAJOBS_API_KEY and Config.USAJOBS_EMAIL)

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls USAJobs API: https://data.usajobs.gov/api/search
        """
        if not self.is_available():
            return list()

        results = []
        try:
            url = "https://data.usajobs.gov/api/search"
            # USAJobs requires specific headers
            headers = {
                "Host": "data.usajobs.gov",
                "User-Agent": Config.USAJOBS_EMAIL,
                "Authorization-Key": Config.USAJOBS_API_KEY
            }
            params = {
                "Keyword": query,
                "LocationName": "Salt Lake City, UT",
            }
            
            response = http_session.get(url, params=params, headers=headers, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            search_result_items = data.get("SearchResult", {}).get("SearchResultItems", [])
            for item in search_result_items:
                body = item.get("MatchedObjectDescriptor", {})
                res = SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=body.get("PositionTitle", ""),
                    url=body.get("PositionURI", ""),
                    snippet=body.get("QualificationSummary", ""),
                    source_name=body.get("OrganizationName", "USAJobs"),
                    published_date=body.get("PublicationStartdate"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=0.0 # Free API
                )
                results.append(res)
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"USAJobs search failed with HTTP error: {e.response.status_code}")
            raise e
        except Exception as e:
            logger.error(f"USAJobs search failed: {e}")
            
        return results

usajobs_provider = UsajobsProvider()
