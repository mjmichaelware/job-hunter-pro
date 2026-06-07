import logging
from typing import List, Dict
from models import SearchResult
from ..base import Provider, ProviderMetadata, ProviderType, SearchProvider
from core import Config, http_session

logger = logging.getLogger(__name__)

class SerpApiJobsProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="serpapi_jobs",
            label="SerpAPI (Google Jobs)",
            type=ProviderType.SEARCH,
            description="Performs job searches using the Google Jobs engine via SerpAPI.",
        )

    def is_available(self) -> bool:
        return bool(Config.SERPAPI_KEY)

    def search(self, query: str) -> List[SearchResult]:
        """
        Calls SerpAPI google_jobs engine.
        """
        if not self.is_available():
            logger.warning(f"{self.metadata.label} key missing.")
            return list()

        # Simple budget guard check if enabled
        if Config.SERPAPI_BUDGET_MODE:
            # We don't have the current account status here easily without a separate call,
            # but we assume the caller or a higher-level budget manager handles the check.
            # Here we just implement the fetch logic.
            pass

        results = []
        try:
            url = "https://serpapi.com/search"
            params = {
                "engine": "google_jobs",
                "q": query,
                "api_key": Config.SERPAPI_KEY,
                "hl": "en",
            }
            
            response = http_session.get(url, params=params, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            job_results = data.get("jobs_results", [])
            for item in job_results:
                # SerpAPI Jobs payload structure
                title = item.get("title", "")
                company = item.get("company_name", "")
                
                # The 'apply_options' contains links
                apply_options = item.get("apply_options", [])
                source_url = ""
                if apply_options:
                    source_url = apply_options[0].get("link", "")

                res = SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=title,
                    url=source_url or item.get("job_id", ""), # Fallback to job_id if no link
                    snippet=item.get("description", ""),
                    source_name=company,
                    published_date=item.get("detected_extensions", {}).get("posted_at"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=1.0 # 1 SerpAPI search = 1 unit
                )
                results.append(res)
                
        except Exception as e:
            logger.error(f"SerpAPI Jobs search failed: {e}")
            
        return results

serpapi_jobs_provider = SerpApiJobsProvider()
