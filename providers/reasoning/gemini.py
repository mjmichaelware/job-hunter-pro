from typing import List, Dict, Any
from ..base import ProviderMetadata, ProviderType, ReasoningProvider
from core import Config

class GeminiProvider(ReasoningProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="gemini",
            label="Google Gemini",
            type=ProviderType.REASONING,
            description="Classification and enrichment via Google Gemini models.",
        )

    def is_available(self) -> bool:
        return bool(Config.GEMINI_API_KEY)

    def classify(self, text_content: str, categories: List[str]) -> Dict[str, Any]:
        # Stub implementation for S3
        return {"provider_stub": self.metadata.key, "category": categories[0] if categories else None}

    def enrich(self, text_content: str) -> Dict[str, Any]:
        # Stub implementation for S3
        return {"provider_stub": self.metadata.key, "enrichment": "stub"}

gemini_provider = GeminiProvider()
