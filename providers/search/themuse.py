import logging
import os
from typing import List
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure
from core import http_session
from core.errors import ProviderHardFailure

logger = logging.getLogger(__name__)

# The Muse paginates ~20 results/page. Pull several pages for real volume.
THEMUSE_MAX_PAGES = int(os.environ.get("THEMUSE_MAX_PAGES", "10"))
# Bias toward the owner's region; comma-list of "City, ST" Muse location strings.
THEMUSE_LOCATIONS = [
    s.strip() for s in os.environ.get("THEMUSE_LOCATIONS", "Salt Lake City, UT").split(";") if s.strip()
]

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

    def _is_specific(self, query: str) -> List[str]:
        """Specific (>3 char, non-generic) terms used to keyword-filter results.

        Broad seeds like 'jobs'/'hiring' return [] so we do NOT over-filter and
        instead return every result the location query produced.
        """
        generic = {"jobs", "job", "hiring", "near", "full", "time", "part", "work", "careers", "career"}
        return [w for w in query.lower().split() if len(w) > 3 and w not in generic]

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls The Muse public API across multiple pages and locations to return
        real volume (the old version pulled a single page of ~20 global results
        and then keyword-filtered most away).
        """
        url = "https://www.themuse.com/api/public/jobs"
        terms = self._is_specific(query)
        locations = THEMUSE_LOCATIONS or [None]
        results: List[SearchResult] = []
        seen = set()
        try:
            for location in locations:
                for page in range(THEMUSE_MAX_PAGES):
                    params = {"page": page}
                    if location:
                        params["location"] = location
                    response = http_session.get(url, params=params, timeout=10)
                    check_hard_failure(self.metadata.key, response)
                    response.raise_for_status()
                    data = response.json()
                    items = data.get("results", []) or []
                    if not items:
                        break  # past the last page for this location
                    for item in items:
                        title = item.get("name", "")
                        landing = item.get("refs", {}).get("landing_page", "")
                        key = landing or title
                        if key in seen:
                            continue
                        if terms:
                            hay = (title + " " + str(item.get("contents", ""))).lower()
                            if not any(t in hay for t in terms):
                                continue
                        seen.add(key)
                        results.append(SearchResult(
                            provider=self.metadata.key,
                            query=query,
                            title=title,
                            url=landing,
                            snippet=item.get("contents", ""),
                            source_name=(item.get("company") or {}).get("name", "The Muse"),
                            published_date=item.get("publication_date"),
                            raw_json=item,
                            confidence=1.0,
                            cost_units=0.0,
                        ))
                    total_pages = data.get("page_count")
                    if total_pages is not None and page + 1 >= total_pages:
                        break

        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error(f"The Muse search failed: {e}")

        return results

themuse_provider = TheMuseProvider()
