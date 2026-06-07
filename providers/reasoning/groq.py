from typing import List, Dict, Any
from ..base import ProviderMetadata, ProviderType, ReasoningProvider
from core import Config

class GroqProvider(ReasoningProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="groq",
            label="Groq",
            type=ProviderType.REASONING,
            description="Fast inference for classification and enrichment via Groq.",
        )

    def is_available(self) -> bool:
        return bool(Config.GROQ_API_KEY)

    def classify(self, text_content: str, categories: List[str]) -> Dict[str, Any]:
        # Stub implementation for S3
        return {"provider_stub": self.metadata.key, "category": categories[0] if categories else None}

    def enrich(self, text_content: str) -> Dict[str, Any]:
        # Stub implementation for S3
        return {"provider_stub": self.metadata.key, "enrichment": "stub"}

groq_provider = GroqProvider()
