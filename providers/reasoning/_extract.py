"""Shared extraction helpers for job-enrichment reasoning providers.

Every provider returns the same envelope:
    {"provider", "mode": "enrich", "confidence", "evidence_required",
     "enrichment": {...}, "source_text_hash", "input_length",
     "model", "ai_enriched"}

``ai_enriched`` is True only when a live LLM call produced the enrichment;
otherwise a regex/heuristic extraction from the exact listing text is used so
cards always gain real (never fabricated) information.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional

MAX_INPUT_CHARS = 7000

JOB_SYSTEM_PROMPT = (
    "You extract structured facts about a single job posting for a job board. "
    "Return ONLY one JSON object. Never invent facts: use only the listing text "
    "and web context provided. Use \"\" or [] when a field is not stated."
)

JOB_USER_TEMPLATE = """Job title: {title}
Company: {company}
Known location / place of work: {location}
Source provider: {provider}

--- LISTING TEXT (from the exact source) ---
{listing}

--- WEB CONTEXT (search results for this title + place of work) ---
{web}

Return this exact JSON schema:
{{
  "summary": "2-4 sentence plain description of the role, main duties, and place of work",
  "salary": "exact pay text if stated (e.g. '$18-$22/hr'), else ''",
  "employment_type": "full-time | part-time | contract | temporary | internship | ''",
  "shift": "shift/schedule if stated (e.g. 'Weekends, 4pm-10pm'), else ''",
  "seniority": "entry | mid | senior | manager | ''",
  "requirements": ["up to 6 concrete requirements stated in the listing"],
  "benefits": ["up to 6 benefits/perks mentioned"],
  "tags": ["up to 8 short role/industry tags"],
  "company_info": "1-2 sentences about the employer from the text/context, else ''",
  "workplace": "neighborhood/place-of-work details (cross streets, mall, airport, building), else ''",
  "contact": "phone/website if listed, else ''"
}}"""

_LIST_KEYS = ("requirements", "benefits", "tags")
_STR_KEYS = (
    "summary", "salary", "employment_type", "shift", "seniority",
    "company_info", "workplace", "contact",
)

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.S)
_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.S)

_SALARY_RE = re.compile(
    r"\$\s?\d{1,3}(?:\.\d{1,2})?(?:\s?[-–—]\s?\$?\d{1,3}(?:\.\d{1,2})?)?"
    r"(?:\s?/\s?(?:hr|hour|yr|year)| per (?:hour|year)| an hour|/ ?hour)?",
    re.I,
)
_SHIFT_WORDS = (
    "overnight", "night shift", "evening", "morning", "weekend", "weekday",
    "day shift", "swing", "rotating", "on-call", "1st shift", "2nd shift",
    "3rd shift", "part-time", "full-time", "flexible schedule",
)
_EMPLOYMENT_WORDS = (
    ("full-time", "full-time"), ("full time", "full-time"),
    ("part-time", "part-time"), ("part time", "part-time"),
    ("contract", "contract"), ("temporary", "temporary"),
    ("seasonal", "seasonal"), ("internship", "internship"),
    ("intern", "internship"), ("per diem", "per-diem"), ("prn", "per-diem"),
)
_BENEFIT_WORDS = (
    "health insurance", "dental", "vision", "401k", "401(k)", "pto",
    "paid time off", "paid vacation", "free meals", "meal discount",
    "employee discount", "tuition", "flexible schedule", "tips", "bonus",
    "signing bonus", "housing", "relocation", "paid training", "insurance",
)
_TAG_WORDS = (
    "server", "waiter", "waitress", "bartender", "barista", "host", "hostess",
    "busser", "food runner", "line cook", "prep cook", "cook", "chef",
    "dishwasher", "cashier", "retail", "warehouse", "driver", "delivery",
    "customer service", "call center", "receptionist", "front desk",
    "housekeeping", "janitorial", "security", "maintenance", "teacher",
    "tutor", "nurse", "caregiver", "sales", "manager", "supervisor",
)
_REQUIREMENT_HINTS = (
    "must ", "required", "requirement", "qualification", "experience",
    "ability to", "able to", "preferred", "minimum",
)
_BULLET_RE = re.compile(r"^[\s\-\u2022\*\d.)]+")


def source_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", "ignore")).hexdigest()[:12]


_PLACEHOLDER_KEYS = {"fake", "test", "dummy", "changeme", "none", "null", "example"}


def is_placeholder_key(key: str) -> bool:
    """True for empty/test keys so unit tests and offline runs never call out."""
    candidate = (key or "").strip()
    return (not candidate) or candidate.lower() in _PLACEHOLDER_KEYS or len(candidate) < 16


def build_messages(
    listing: str,
    title: str = "",
    company: str = "",
    location: str = "",
    provider: str = "",
    web_context: str = "",
) -> List[Dict[str, str]]:
    user = JOB_USER_TEMPLATE.format(
        title=title or "(unknown)",
        company=company or "(unknown)",
        location=location or "(unknown)",
        provider=provider or "(unknown)",
        listing=(listing or "")[:MAX_INPUT_CHARS],
        web=(web_context or "(none)")[:2500],
    )
    return [
        {"role": "system", "content": JOB_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def build_prompt(**kwargs: Any) -> str:
    """Single-string prompt for providers that don't use chat messages."""
    return JOB_SYSTEM_PROMPT + "\n\n" + JOB_USER_TEMPLATE.format(
        title=kwargs.get("title") or "(unknown)",
        company=kwargs.get("company") or "(unknown)",
        location=kwargs.get("location") or "(unknown)",
        provider=kwargs.get("provider") or "(unknown)",
        listing=(kwargs.get("listing") or "")[:MAX_INPUT_CHARS],
        web=(kwargs.get("web_context") or "(none)")[:2500],
    )


def parse_json_payload(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    candidate = ""
    fence = _FENCE_RE.search(text)
    if fence:
        candidate = fence.group(1)
    else:
        match = _JSON_BLOCK_RE.search(text)
        if match:
            candidate = match.group(0)
    if not candidate:
        return None
    try:
        payload = json.loads(candidate)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def normalize_enrichment(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    payload = payload or {}
    for key in _STR_KEYS:
        value = payload.get(key)
        out[key] = value.strip() if isinstance(value, str) else ""
    for key in _LIST_KEYS:
        value = payload.get(key)
        if isinstance(value, list):
            out[key] = [str(v).strip() for v in value if str(v).strip()][:8]
        elif isinstance(value, str) and value.strip():
            out[key] = [v.strip() for v in re.split(r"[;,]\s*", value) if v.strip()][:8]
        else:
            out[key] = []
    return out


def heuristic_enrichment(text: str) -> Dict[str, Any]:
    """Deterministic extraction from the exact listing text (no LLM)."""
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    out: Dict[str, Any] = {key: "" for key in _STR_KEYS}
    for key in _LIST_KEYS:
        out[key] = []

    sentences = re.split(r"(?<=[.!?])\s+", clean)
    out["summary"] = " ".join(sentences[:3])[:420].strip()

    salary = _SALARY_RE.search(clean)
    out["salary"] = salary.group(0).strip() if salary else ""

    lowered = clean.lower()
    for word in _SHIFT_WORDS:
        if word in lowered:
            out["shift"] = word
            break
    for needle, label in _EMPLOYMENT_WORDS:
        if needle in lowered:
            out["employment_type"] = label
            break

    out["benefits"] = [b for b in _BENEFIT_WORDS if b in lowered][:8]
    if not out["tags"]:
        out["tags"] = [t for t in _TAG_WORDS if t in lowered][:8]

    lines = re.split(r"[\n\r]+", str(text or ""))
    requirements: List[str] = []
    for line in lines:
        stripped = _BULLET_RE.sub("", line).strip()
        if not (12 <= len(stripped) <= 220):
            continue
        if any(hint in stripped.lower() for hint in _REQUIREMENT_HINTS):
            requirements.append(stripped)
        if len(requirements) >= 6:
            break
    out["requirements"] = requirements

    return out


def envelope(
    provider_key: str,
    text: str,
    enrichment: Dict[str, Any],
    confidence: float,
    model: str = "",
    ai_enriched: bool = False,
) -> Dict[str, Any]:
    return {
        "provider": provider_key,
        "mode": "enrich",
        "confidence": confidence,
        "evidence_required": True,
        "enrichment": normalize_enrichment(enrichment),
        "source_text_hash": source_hash(text),
        "input_length": len(text or ""),
        "model": model,
        "ai_enriched": bool(ai_enriched),
    }


def unavailable(provider_key: str, text: str, mode: str = "enrich") -> Dict[str, Any]:
    return {
        "provider": provider_key,
        "mode": mode,
        "available": False,
        "confidence": 0.0,
        "evidence_required": True,
        "enrichment": {} if mode == "enrich" else None,
        "source_text_hash": source_hash(text),
        "input_length": len(text or ""),
        "ai_enriched": False,
    }


def merge_with_heuristic(
    llm_payload: Optional[Dict[str, Any]], text: str
) -> Dict[str, Any]:
    """LLM fields win; heuristic fills anything the LLM left blank."""
    llm = normalize_enrichment(llm_payload)
    heur = heuristic_enrichment(text)
    merged = dict(heur)
    for key in _STR_KEYS:
        if llm.get(key):
            merged[key] = llm[key]
    for key in _LIST_KEYS:
        if llm.get(key):
            merged[key] = llm[key]
    return merged
