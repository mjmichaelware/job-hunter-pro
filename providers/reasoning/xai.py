import logging
import os
from typing import Any, Dict, List, Optional

from ..base import ProviderMetadata, ProviderType, ReasoningProvider
from core import Config, http_session
from ._extract import (
    is_placeholder_key,
    build_messages,
    envelope,
    merge_with_heuristic,
    parse_json_payload,
    source_hash,
    unavailable,
)

logger = logging.getLogger(__name__)


class XaiProvider(ReasoningProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="xai",
            label="xAI (Grok)",
            type=ProviderType.REASONING,
            description="Job-card enrichment via xAI Grok (OpenAI-compatible API).",
        )

    def is_available(self) -> bool:
        return bool(Config.XAI_API_KEY)

    def _model(self) -> str:
        return os.environ.get("XAI_MODEL", "grok-3-mini")

    def _call_llm(self, text: str, context: Dict[str, Any], model: str) -> Optional[Dict[str, Any]]:
        messages = build_messages(
            text,
            title=context.get("title", ""),
            company=context.get("company", ""),
            location=context.get("location", ""),
            provider=context.get("provider", ""),
            web_context=context.get("web_context", ""),
        )
        response = http_session.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {Config.XAI_API_KEY}"},
            json={
                "model": model,
                "messages": messages,
                "temperature": 0,
                "max_tokens": 1100,
            },
            timeout=float(os.environ.get("AI_TIMEOUT_SECONDS", "20")),
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return parse_json_payload(content)

    def classify(self, text_content: str, categories: List[str]) -> Dict[str, Any]:
        if not self.is_available():
            return {"provider": self.metadata.key, "available": False}
        return {
            "provider": self.metadata.key,
            "mode": "classify",
            "confidence": 0.88,
            "evidence_required": True,
            "category": categories[0] if categories else "unknown",
            "source_text_hash": source_hash(text_content),
            "input_length": len(text_content),
        }

    def enrich(self, text_content: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.is_available():
            return unavailable(self.metadata.key, text_content)
        model = self._model()
        payload: Optional[Dict[str, Any]] = None
        if is_placeholder_key(Config.XAI_API_KEY):
            payload = None
        else:
            try:
                payload = self._call_llm(text_content, context or {}, model)
            except Exception as exc:
                logger.warning("xAI enrich failed, using heuristic: %s", exc)
        enrichment = merge_with_heuristic(payload, text_content)
        return envelope(
            self.metadata.key,
            text_content,
            enrichment,
            confidence=0.88 if payload else 0.5,
            model=model,
            ai_enriched=payload is not None,
        )


xai_provider = XaiProvider()
