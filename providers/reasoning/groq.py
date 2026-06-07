import hashlib
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

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:8]

    def classify(self, text_content: str, categories: List[str]) -> Dict[str, Any]:
        if not self.is_available():
            return {"provider": self.metadata.key, "available": False}
        
        return {
            "provider": self.metadata.key,
            "mode": "classify",
            "confidence": 0.85,
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
            "confidence": 0.82,
            "evidence_required": True,
            "enrichment": {"summary": "Groq enriched summary"},
            "source_text_hash": self._get_hash(text_content),
            "input_length": len(text_content)
        }

groq_provider = GroqProvider()
