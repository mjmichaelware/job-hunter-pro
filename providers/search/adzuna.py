import logging
from typing import List
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure
from core import Config, http_session
from core.errors import ProviderHardFailure

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

        # Adzuna paginates by URL path (/search/<page>) and supports up to 50
        # results_per_page. Pull several pages for real volume + wider Utah net.
        import os
        max_pages = int(os.environ.get("ADZUNA_MAX_PAGES", "3"))
        where = os.environ.get("ADZUNA_WHERE", "Salt Lake City")
        distance = os.environ.get("ADZUNA_DISTANCE_KM", "80")  # ~50mi, covers Utah metro

        results = []
        seen = set()
        try:
            for page in range(1, max_pages + 1):
                url = f"https://api.adzuna.com/v1/api/jobs/us/search/{page}"
                params = {
                    "app_id": Config.ADZUNA_APP_ID,
                    "app_key": Config.ADZUNA_APP_KEY,
                    "what": query,
                    "where": where,
                    "distance": distance,
                    "results_per_page": 50,
                    "content-type": "application/json",
                }
                response = http_session.get(url, params=params, timeout=Config.REQUEST_TIMEOUT)
                check_hard_failure(self.metadata.key, response)
                response.raise_for_status()
                data = response.json()
                items = data.get("results", []) or []
                if not items:
                    break
                for item in items:
                    rurl = item.get("redirect_url", "")
                    if rurl in seen:
                        continue
                    seen.add(rurl)
                    results.append(SearchResult(
                        provider=self.metadata.key,
                        query=query,
                        title=item.get("title", ""),
                        url=rurl,
                        snippet=item.get("description", ""),
                        source_name=(item.get("company") or {}).get("display_name"),
                        published_date=item.get("created"),
                        raw_json=item,
                        confidence=1.0,
                        cost_units=1.0,
                    ))

        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error(f"Adzuna search failed: {e}")

        return results

adzuna_provider = AdzunaProvider()
