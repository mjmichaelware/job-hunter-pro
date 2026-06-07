from typing import List
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider
from core import Config

class JoobleProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="jooble",
            label="Jooble",
            type=ProviderType.SEARCH,
            description="Worldwide job aggregator.",
        )

    def is_available(self) -> bool:
        return bool(Config.JOOBLE_API_KEY)

    def search(self, query: str) -> List[SearchResult]:
        # Stub implementation for S3
        return []

jooble_provider = JoobleProvider()
