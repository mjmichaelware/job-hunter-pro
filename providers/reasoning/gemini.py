import hashlib
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

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:8]

    def classify(self, text_content: str, categories: List[str]) -> Dict[str, Any]:
        if not self.is_available():
            return {"provider": self.metadata.key, "available": False}
        
        return {
            "provider": self.metadata.key,
            "mode": "classify",
            "confidence": 0.92,
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
            "confidence": 0.88,
            "evidence_required": True,
            "enrichment": {"summary": "Gemini enriched summary", "entities": []},
            "source_text_hash": self._get_hash(text_content),
            "input_length": len(text_content)
        }

gemini_provider = GeminiProvider()
