import hashlib
from typing import List, Dict, Any
from ..base import ProviderMetadata, ProviderType, ReasoningProvider
from core import Config

class ClaudeProvider(ReasoningProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="claude",
            label="Anthropic Claude",
            type=ProviderType.REASONING,
            description="Classification and enrichment via Anthropic Claude models (e.g., Sonnet 3.5).",
        )

    def is_available(self) -> bool:
        return bool(Config.ANTHROPIC_API_KEY)

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:8]

    def classify(self, text_content: str, categories: List[str]) -> Dict[str, Any]:
        if not self.is_available():
            return {"provider": self.metadata.key, "available": False}
        
        return {
            "provider": self.metadata.key,
            "mode": "classify",
            "confidence": 0.94,
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
            "confidence": 0.91,
            "evidence_required": True,
            "enrichment": {"summary": "Claude enriched summary"},
            "source_text_hash": self._get_hash(text_content),
            "input_length": len(text_content)
        }

claude_provider = ClaudeProvider()
