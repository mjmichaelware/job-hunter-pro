from typing import List
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider
from core import Config

class AdzunaProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="adzuna",
            label="Adzuna",
            type=ProviderType.SEARCH,
            description="Job search provider Adzuna.",
        )

    def is_available(self) -> bool:
        return bool(Config.ADZUNA_APP_ID and Config.ADZUNA_APP_KEY)

    def search(self, query: str) -> List[SearchResult]:
        # Stub implementation for S3
        return []

adzuna_provider = AdzunaProvider()
