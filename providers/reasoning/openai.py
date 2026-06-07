from typing import List, Dict, Any
from ..base import ProviderMetadata, ProviderType, ReasoningProvider
from core import Config

class OpenaiProvider(ReasoningProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="openai",
            label="OpenAI",
            type=ProviderType.REASONING,
            description="Classification and enrichment via OpenAI models (e.g., GPT-4o).",
        )

    def is_available(self) -> bool:
        return bool(Config.OPENAI_API_KEY)

    def classify(self, text_content: str, categories: List[str]) -> Dict[str, Any]:
        # Stub implementation for S3
        print(f"STUB: Classifying with {self.metadata.label}")
        return {"provider_stub": self.metadata.key, "category": categories[0] if categories else None}

    def enrich(self, text_content: str) -> Dict[str, Any]:
        # Stub implementation for S3
        return {"provider_stub": self.metadata.key, "enrichment": "stub"}

openai_provider = OpenaiProvider()
