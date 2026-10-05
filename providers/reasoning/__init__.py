"""Reasoning-provider chain used for post-discovery job-card hydration.

``enrich_listing`` tries every keyed provider in speed order and returns the
first result that was actually produced by a live LLM call (``ai_enriched``).
If none succeed, the best heuristic extraction is returned so cards always
gain real information.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

_ORDER = ("groq", "gemini", "openai", "xai", "claude")


def get_reasoning_providers() -> List[Any]:
    from .groq import groq_provider
    from .gemini import gemini_provider
    from .openai import openai_provider
    from .xai import xai_provider
    from .claude import claude_provider

    return [groq_provider, gemini_provider, openai_provider, xai_provider, claude_provider]


def enrich_listing(text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    best_heuristic: Optional[Dict[str, Any]] = None
    for provider in get_reasoning_providers():
        try:
            if not provider.is_available():
                continue
            try:
                result = provider.enrich(text, context=context)
            except TypeError:
                result = provider.enrich(text)
            if result.get("ai_enriched"):
                return result
            if best_heuristic is None:
                best_heuristic = result
        except Exception:
            continue
    if best_heuristic is not None:
        return best_heuristic
    from ._extract import envelope, heuristic_enrichment

    return envelope(
        "heuristic", text, heuristic_enrichment(text),
        confidence=0.4, model="regex", ai_enriched=False,
    )
