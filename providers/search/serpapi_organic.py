from typing import List, Dict
from models import SearchResult
from ..base import Provider, ProviderMetadata, ProviderType, SearchProvider
from core import Config

class SerpApiOrganicProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="serpapi_organic",
            label="SerpAPI (Google Organic)",
            type=ProviderType.SEARCH,
            description="Performs organic web searches via SerpAPI. Budget-gated by default.",
        )

    def is_available(self) -> bool:
        return bool(Config.SERPAPI_KEY)

    def search(self, query: str) -> List[SearchResult]:
        # Stub implementation for S3
        print(f"STUB: Searching {self.metadata.label} for '{query}'")
        return []

serpapi_organic_provider = SerpApiOrganicProvider()
