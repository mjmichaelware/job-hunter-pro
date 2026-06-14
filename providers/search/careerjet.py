import logging
from typing import List
from models import SearchResult
import os
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure
from core import Config, http_session
from core.errors import ProviderHardFailure

logger = logging.getLogger(__name__)

def _enabled() -> bool:
    return str(os.environ.get("ENABLE_CAREERJET", "")).strip() in {"1", "true", "True", "yes", "on"}

class CareerjetProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="careerjet",
            label="Careerjet",
            type=ProviderType.SEARCH,
            description="International job search engine. OFF by default (upstream not working); set ENABLE_CAREERJET=1 once fixed.",
        )

    def disabled_reason(self) -> str:
        # Owner reports this upstream does not work; keep it off so it never
        # blocks the run. Flip on with ENABLE_CAREERJET=1 when the source is fixed.
        return "" if _enabled() else "off_by_default (ENABLE_CAREERJET=1 to enable)"

    def is_available(self) -> bool:
        return _enabled() and bool(Config.CAREERJET_AFFID)

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls Careerjet API: http://public.api.careerjet.net/search
        """
        if not self.is_available():
            return list()

        results = []
        try:
            import os
            url = "http://public.api.careerjet.net/search"
            # Careerjet requires user_ip and user_agent; supports pagesize (max 99).
            params = {
                "affid": Config.CAREERJET_AFFID,
                "keywords": query,
                "location": os.environ.get("CAREERJET_LOCATION", "Utah"),
                "pagesize": os.environ.get("CAREERJET_PAGESIZE", "99"),
                "user_ip": "127.0.0.1",
                "user_agent": "JobHunterPro/1.0"
            }
            
            response = http_session.get(url, params=params, timeout=Config.REQUEST_TIMEOUT)
            check_hard_failure(self.metadata.key, response)
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

        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error(f"Careerjet search failed: {e}")

        return results

careerjet_provider = CareerjetProvider()
