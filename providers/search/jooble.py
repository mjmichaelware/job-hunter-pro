import logging
from typing import List
from models import SearchResult
import os
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure
from core import Config, http_session
from core.errors import ProviderHardFailure

logger = logging.getLogger(__name__)

def _enabled() -> bool:
    return str(os.environ.get("ENABLE_JOOBLE", "")).strip() in {"1", "true", "True", "yes", "on"}

class JoobleProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="jooble",
            label="Jooble",
            type=ProviderType.SEARCH,
            description="Worldwide job aggregator. OFF by default (upstream not working); set ENABLE_JOOBLE=1 once fixed.",
        )

    def disabled_reason(self) -> str:
        # Owner reports this upstream does not work; keep it off so it never
        # blocks the run. Flip on with ENABLE_JOOBLE=1 when the source is fixed.
        return "" if _enabled() else "off_by_default (ENABLE_JOOBLE=1 to enable)"

    def is_available(self) -> bool:
        return _enabled() and bool(Config.JOOBLE_API_KEY)

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls Jooble API: https://jooble.org/api/queries/v1/us
        """
        if not self.is_available():
            return list()

        import os
        max_pages = int(os.environ.get("JOOBLE_MAX_PAGES", "3"))
        location = os.environ.get("JOOBLE_LOCATION", "Utah")
        results = []
        seen = set()
        try:
            url = f"https://jooble.org/api/queries/v1/us/{Config.JOOBLE_API_KEY}"
            for page in range(1, max_pages + 1):
                # Jooble uses POST with JSON body; supports page + ResultOnPage.
                payload = {
                    "keywords": query,
                    "location": location,
                    "page": page,
                    "ResultOnPage": 50,
                }
                response = http_session.post(url, json=payload, timeout=Config.REQUEST_TIMEOUT)
                check_hard_failure(self.metadata.key, response)
                response.raise_for_status()
                data = response.json()
                jobs = data.get("jobs", []) or []
                if not jobs:
                    break
                for item in jobs:
                    link = item.get("link", "")
                    if link in seen:
                        continue
                    seen.add(link)
                    results.append(SearchResult(
                        provider=self.metadata.key,
                        query=query,
                        title=item.get("title", ""),
                        url=link,
                        snippet=item.get("snippet", ""),
                        source_name=item.get("company", "Jooble"),
                        published_date=item.get("updated"),
                        raw_json=item,
                        confidence=1.0,
                        cost_units=1.0,
                    ))

        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error(f"Jooble search failed: {e}")

        return results

jooble_provider = JoobleProvider()
