from typing import List
from models import SearchResult
from ..base import ProviderMetadata, ProviderType, SearchProvider
from core import Config

class UsajobsProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="usajobs",
            label="USAJobs",
            type=ProviderType.SEARCH,
            description="Job search for US federal government positions.",
        )

    def is_available(self) -> bool:
        return bool(Config.USAJOBS_API_KEY and Config.USAJOBS_EMAIL)

    def search(self, query: str) -> List[SearchResult]:
        # Stub implementation for S3
        return []

usajobs_provider = UsajobsProvider()
