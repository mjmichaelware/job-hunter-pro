from typing import List
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider
from core import Config

class CareerjetProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="careerjet",
            label="Careerjet",
            type=ProviderType.SEARCH,
            description="International job search engine.",
        )

    def is_available(self) -> bool:
        return bool(Config.CAREERJET_AFFID)

    def search(self, query: str) -> List[SearchResult]:
        # Stub implementation for S3
        return []

careerjet_provider = CareerjetProvider()
