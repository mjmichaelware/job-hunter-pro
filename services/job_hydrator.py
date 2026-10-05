"""Universal deep-hydration engine for accepted jobs.

For each job, fills the info card with as much real information as possible:

  1. Place resolution — Google Places text search for the employer near 84115,
     then Haversine radius + a UTA-style commute estimate.
  2. Source scrape — fetch the exact source listing URL and extract its text
     when the provider snippet is thin.
  3. Web research — SerpAPI organic search against the job title + place of
     work (bounded per run; skipped when no key/quota).
  4. LLM extraction — OpenAI / Gemini / Groq / xAI (first available that
     answers) turns the listing + web context into structured fields:
     summary, salary, employment_type, shift, seniority, requirements,
     benefits, tags, company_info, workplace, contact.
  5. Deterministic fallback — if every LLM fails, a regex extractor still
     pulls salary/shift/benefits/requirements from the exact listing text.

Enrichment provenance lands on the job: ``ai_provider``, ``ai_enriched``,
``enrichment_model``, ``enriched_at``, ``web_research``.
"""

from __future__ import annotations

import concurrent.futures
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core import http_session
from geo.haversine import haversine_distance

logger = logging.getLogger(__name__)

# 84115 origin (28 E Bryan Ave, Salt Lake City, UT).
ORIGIN_LATLNG = (40.7106, -111.8867)

_SCRIPT_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I | re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_ENTITY_RE = re.compile(r"&(?:nbsp|amp|quot|#39|lt|gt);?", re.I)
_ENTITY_MAP = {
    "&nbsp;": " ", "&nbsp": " ", "&amp;": "&", "&amp": "&",
    "&quot;": '"', "&quot": '"', "&#39;": "'", "&#39": "'",
    "&lt;": "<", "&lt": "<", "&gt;": ">", "&gt": ">",
}

_research_lock = threading.Lock()
_research_budget = {"remaining": 5}
_hydrate_deadline = {"ts": float("inf")}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value if value is not None else "")).strip()


def _html_to_text(html: str) -> str:
    text = _SCRIPT_RE.sub(" ", html or "")
    text = _TAG_RE.sub(" ", text)
    text = _ENTITY_RE.sub(lambda m: _ENTITY_MAP.get(m.group(0).lower(), " "), text)
    return _clean(text)


def _scrape(url: str) -> str:
    if not url or not str(url).startswith("http"):
        return ""
    try:
        response = http_session.get(
            url,
            timeout=float(os.environ.get("HYDRATE_SCRAPE_TIMEOUT", "6")),
            headers={"User-Agent": "Mozilla/5.0 (compatible; JobHunterPro/1.0)"},
        )
        if response.status_code == 200:
            return _html_to_text(response.text)[:7000]
    except Exception as exc:
        logger.debug("scrape failed for %s: %s", url, exc)
    return ""


def _places(query: str) -> Optional[Dict[str, Any]]:
    """Dict-shaped Places lookup from api.index (cached, respects Maps key)."""
    if not query:
        return None
    try:
        from api.index import places_text_search

        return places_text_search(query)
    except Exception:
        return None


def _web_research(title: str, company: str, location: str) -> str:
    """Bounded SerpAPI organic research: job title + place of work."""
    if os.environ.get("HYDRATE_WEB_RESEARCH", "1").strip() == "0":
        return ""
    with _research_lock:
        if _research_budget["remaining"] <= 0:
            return ""
        _research_budget["remaining"] -= 1
    try:
        from providers.search.serpapi_organic import serpapi_organic_provider

        if not serpapi_organic_provider.is_available():
            return ""
        query = " ".join(part for part in (title, company, location, "hiring") if part)[:160]
        results = serpapi_organic_provider.search(query)
        lines: List[str] = []
        for item in results[:5]:
            item_title = _clean(getattr(item, "title", "") or "")
            snippet = _clean(getattr(item, "snippet", "") or "")
            url = _clean(getattr(item, "url", "") or "")
            if item_title or snippet:
                lines.append(f"- {item_title}: {snippet} ({url})")
        return "\n".join(lines)
    except Exception as exc:
        logger.debug("web research failed: %s", exc)
        return ""


def _llm_enrich(job: Dict[str, Any], listing: str, web_context: str) -> Dict[str, Any]:
    context = {
        "title": _clean(job.get("title")),
        "company": _clean(job.get("company")),
        "location": _clean(
            job.get("resolved_address") or job.get("location") or job.get("listing_location")
        ),
        "provider": _clean(job.get("_provider") or job.get("via")),
        "web_context": web_context,
    }
    try:
        from providers.reasoning import enrich_listing

        return enrich_listing(listing, context=context)
    except Exception as exc:
        logger.warning("reasoning chain unavailable: %s", exc)
        from providers.reasoning._extract import envelope, heuristic_enrichment

        return envelope(
            "heuristic", listing, heuristic_enrichment(listing),
            confidence=0.4, model="regex", ai_enriched=False,
        )


def _apply_enrichment(job: Dict[str, Any], result: Dict[str, Any]) -> None:
    enrichment = result.get("enrichment") or {}
    summary = _clean(enrichment.get("summary"))
    existing = _clean(job.get("description"))
    if summary and len(summary) > len(existing):
        job["description"] = summary
    job["summary"] = summary or existing[:420]

    current_salary = _clean(job.get("salary"))
    if enrichment.get("salary") and (
        not current_salary or "not listed" in current_salary.lower()
    ):
        job["salary"] = _clean(enrichment["salary"])

    for key in ("employment_type", "shift", "seniority", "company_info", "workplace", "contact"):
        value = _clean(enrichment.get(key))
        if value:
            job[key] = value

    for key in ("requirements", "benefits"):
        values = enrichment.get(key)
        if isinstance(values, list) and values:
            job[key] = values[:8]

    tags = list(dict.fromkeys([*(job.get("tags") or []), *(enrichment.get("tags") or [])]))
    if tags:
        job["tags"] = tags[:10]

    job["ai_provider"] = result.get("provider") or "heuristic"
    job["ai_enriched"] = bool(result.get("ai_enriched"))
    job["enrichment_model"] = result.get("model", "")
    job["enriched_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def hydrate_single_job(job: dict) -> dict:
    """Hydrate a single job with the maximum real information available."""

    # 1. Place resolution + radius + commute estimate when address is missing.
    company = _clean(job.get("company"))
    if not job.get("resolved_address") and company:
        place = _places(f"{company} Salt Lake City UT")
        if place and place.get("latlng"):
            latlng = place["latlng"]
            job["resolved_address"] = _clean(place.get("formatted_address"))
            job["place_id"] = _clean(place.get("place_id"))
            job["place_rating"] = place.get("rating")
            try:
                radius = round(
                    haversine_distance(ORIGIN_LATLNG[0], ORIGIN_LATLNG[1], latlng[0], latlng[1]),
                    2,
                )
                job["radius_miles"] = radius
                job["distance_miles"] = radius
                job["radius_label"] = f"{radius} mi radius"
                commute = int((radius / 14.5) * 3600 + 480)
                job["commute_seconds"] = commute
                job["commute_label"] = f"{round(commute / 60)}m est."
            except Exception:
                pass

    # 2. Gather the richest listing text: provider description + source scrape.
    listing = _clean(job.get("description"))
    url = job.get("source_url") or job.get("url")
    if url and len(listing) < 500:
        scraped = _scrape(str(url))
        if scraped:
            listing = f"{listing} {scraped}".strip()[:7000]
    if not listing:
        listing = _clean(" ".join(filter(None, [
            _clean(job.get("title")),
            company,
            _clean(job.get("location")),
            _clean(job.get("salary")),
        ])))

    # 3. Web research against title + place of work (bounded per run).
    web_context = _web_research(
        _clean(job.get("title")), company, _clean(job.get("location") or job.get("resolved_address"))
    )
    if web_context:
        job["web_research"] = web_context[:1500]

    # 4. LLM structured extraction (with deterministic fallback inside). Once
    # the hydration deadline passes, skip the LLM and use the regex extractor
    # so the batch can never run long.
    if time.time() < _hydrate_deadline["ts"]:
        result = _llm_enrich(job, listing, web_context)
    else:
        from providers.reasoning._extract import envelope, heuristic_enrichment

        result = envelope(
            "heuristic", listing, heuristic_enrichment(listing),
            confidence=0.4, model="regex", ai_enriched=False,
        )
    _apply_enrichment(job, result)

    # 5. Recompute resolution flags honestly.
    flags: List[str] = []
    if not job.get("resolved_address"):
        flags.append("address_unresolved")
    if job.get("radius_miles") is None:
        flags.append("radius_unverified")
    if job.get("commute_seconds") is None:
        flags.append("transit_unverified")
    job["resolution_flags"] = flags
    job["needs_resolution"] = bool(flags)
    return job


def hydrate_all_jobs(jobs: list, max_workers: int = 4, limit: Optional[int] = None) -> list:
    """Hydrate up to ``limit`` jobs concurrently; the rest pass through unchanged."""
    if not jobs:
        return []
    jobs = list(jobs)
    if limit is not None and limit >= 0 and len(jobs) > limit:
        head, tail = jobs[:limit], jobs[limit:]
    else:
        head, tail = jobs, []

    _research_budget["remaining"] = int(os.environ.get("MAX_WEB_RESEARCH", "5"))
    _hydrate_deadline["ts"] = time.time() + float(
        os.environ.get("HYDRATE_DEADLINE_SECONDS", "35")
    )
    workers = max(1, min(int(max_workers or 4), 8))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        hydrated = list(executor.map(hydrate_single_job, head))
    return hydrated + tail
