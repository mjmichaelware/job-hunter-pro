import logging
import os
from typing import Any, Dict, List, Optional

from ..base import ProviderMetadata, ProviderType, ReasoningProvider
from core import Config, http_session
from ._extract import (
    is_placeholder_key,
    build_prompt,
    envelope,
    merge_with_heuristic,
    parse_json_payload,
    source_hash,
    unavailable,
)

logger = logging.getLogger(__name__)


class GeminiProvider(ReasoningProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="gemini",
            label="Google Gemini",
            type=ProviderType.REASONING,
            description="Job-card enrichment via Google Gemini flash models.",
        )

    def is_available(self) -> bool:
        return bool(Config.GEMINI_API_KEY)

    def _model(self) -> str:
        return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    def _call_llm(self, text: str, context: Dict[str, Any], model: str) -> Optional[Dict[str, Any]]:
        prompt = build_prompt(
            listing=text,
            title=context.get("title", ""),
            company=context.get("company", ""),
            location=context.get("location", ""),
            provider=context.get("provider", ""),
            web_context=context.get("web_context", ""),
        )
        generation_config: Dict[str, Any] = {
            "temperature": 0,
            "maxOutputTokens": 2500,
            "responseMimeType": "application/json",
        }
        # Gemini 2.5+ counts "thinking" tokens against maxOutputTokens, which
        # truncates the JSON. Disable thinking for this extraction task.
        if "2.5" in model or "flash" in model:
            generation_config["thinkingConfig"] = {"thinkingBudget": 0}
        response = http_session.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": Config.GEMINI_API_KEY},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": generation_config,
            },
            timeout=float(os.environ.get("AI_TIMEOUT_SECONDS", "20")),
        )
        response.raise_for_status()
        candidates = response.json().get("candidates") or []
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts") or []
        content = "".join(part.get("text", "") for part in parts)
        return parse_json_payload(content)

    def classify(self, text_content: str, categories: List[str]) -> Dict[str, Any]:
        if not self.is_available():
            return {"provider": self.metadata.key, "available": False}
        return {
            "provider": self.metadata.key,
            "mode": "classify",
            "confidence": 0.92,
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
        if is_placeholder_key(Config.GEMINI_API_KEY):
            payload = None
        else:
            try:
                payload = self._call_llm(text_content, context or {}, model)
            except Exception as exc:
                logger.warning("Gemini enrich failed, using heuristic: %s", exc)
        enrichment = merge_with_heuristic(payload, text_content)
        return envelope(
            self.metadata.key,
            text_content,
            enrichment,
            confidence=0.92 if payload else 0.5,
            model=model,
            ai_enriched=payload is not None,
        )


gemini_provider = GeminiProvider()
