from typing import List
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider

class TheMuseProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="themuse",
            label="The Muse",
            type=ProviderType.SEARCH,
            description="Job board with a focus on company culture.",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True # Does not require an API key

    def search(self, query: str) -> List[SearchResult]:
        # Stub implementation for S3
        return []

themuse_provider = TheMuseProvider()
