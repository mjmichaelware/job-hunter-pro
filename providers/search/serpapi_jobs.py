from typing import List, Dict
from models import SearchResult
from ..base import Provider, ProviderMetadata, ProviderType, SearchProvider
from core import Config

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
        # This is a stub implementation for S3. No real HTTP call is made.
        print(f"STUB: Searching {self.metadata.label} for '{query}'")
        return []

serpapi_jobs_provider = SerpApiJobsProvider()
