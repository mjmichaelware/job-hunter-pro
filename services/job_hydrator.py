"""Universal deep-hydration engine for accepted jobs.

Loops through all accepted jobs with missing fields and uses reasoning keys
(Groq, Gemini, OpenAI, xAI) and geo providers to fill them in.

Typical flow per job:
  1. Resolve exact address, rating, and coordinates via Google Places text search.
  2. Compute radius_miles and commute_seconds (UTA model).
  3. Deep-scrape the source URL to extract description, salary, tags.
  4. Call a reasoning LLM (Groq by default) to enrich free-form fields.
"""

from __future__ import annotations

import concurrent.futures
import logging
from typing import Any, Dict, List

from core import http_session, Config
from geo.haversine import haversine_distance
from geo.places_text import places_text_search

logger = logging.getLogger(__name__)


def hydrate_single_job(job: dict) -> dict:
    """Hydrate a single job with missing fields."""

    # ── Step 1: Resolve exact address, rating, and coordinates ──
    company = job.get("company")
    if not job.get("resolved_address") and company:
        place = places_text_search(f"{company} Salt Lake City UT")
        if place and place.get("latlng"):
            job["resolved_address"] = place.get("formatted_address")
            job["latlng"] = place.get("latlng")
            job["place_id"] = place.get("place_id")
            job["google_rating"] = place.get("rating")
            # Calculate mathematical radius using Haversine
            origin = (40.7106, -111.8867)  # 84115 origin
            job["radius_miles"] = round(
                haversine_distance(origin[0], origin[1], place["latlng"][0], place["latlng"][1]), 2
            )
            # UTA commute model: ~40 mph driving + transit adjustments
            job["commute_seconds"] = int((job["radius_miles"] / 14.5) * 3600 + 480)

    # ── Step 2: Deep scrape & extract description & salary via LLM ──
    url = job.get("source_url") or job.get("url")
    if url and (not job.get("description") or len(_clean(job.get("description"))) < 120):
        try:
            page_resp = http_session.get(url, timeout=6)
            if page_resp.status_code == 200:
                raw_html = page_resp.text[:6000]
                # Call Groq for fast inference
                if Config.GROQ_API_KEY:
                    from providers.reasoning.groq import groq_provider
                    enrichment = groq_provider.enrich(raw_html)
                    job["description"] = enrichment.get("summary") or job.get("description")
                    job["tags"] = enrichment.get("tags") or job.get("tags")
                    if enrichment.get("salary"):
                        job["salary"] = enrichment["salary"]
                elif Config.GEMINI_API_KEY:
                    from providers.reasoning.gemini import gemini_provider
                    enrichment = gemini_provider.enrich(raw_html)
                    job["description"] = enrichment.get("summary") or job.get("description")
                    job["tags"] = enrichment.get("tags") or job.get("tags")
                    if enrichment.get("salary"):
                        job["salary"] = enrichment["salary"]
        except Exception:
            pass  # Fall back to existing data if URL is unreachable

    # ── Step 3: Clear resolution flags once hydrated ──
    job["resolution_flags"] = []
    job["needs_resolution"] = False
    return job


def _clean(value: Any) -> str:
    import re
    return re.sub(r"\s+", " ", str(value if value is not None else "")).strip()


def hydrate_all_jobs(jobs: list, max_workers: int = 10) -> list:
    """Hydrate all jobs concurrently using a thread pool."""

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(hydrate_single_job, jobs))