import hashlib
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

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:8]

    def classify(self, text_content: str, categories: List[str]) -> Dict[str, Any]:
        if not self.is_available():
            return {"provider": self.metadata.key, "available": False}
        
        # Real implementation would call OpenAI API here.
        # For R8, we ensure the structure is correct and returns safe output if mocked.
        return {
            "provider": self.metadata.key,
            "mode": "classify",
            "confidence": 0.95,
            "evidence_required": True,
            "category": categories[0] if categories else "unknown",
            "source_text_hash": self._get_hash(text_content),
            "input_length": len(text_content)
        }

    def enrich(self, text_content: str) -> Dict[str, Any]:
        if not self.is_available():
            return {"provider": self.metadata.key, "available": False}

        return {
            "provider": self.metadata.key,
            "mode": "enrich",
            "confidence": 0.9,
            "evidence_required": True,
            "enrichment": {"summary": "Enriched content placeholder", "tags": ["job", "tech"]},
            "source_text_hash": self._get_hash(text_content),
            "input_length": len(text_content)
        }

openai_provider = OpenaiProvider()
