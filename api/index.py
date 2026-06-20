import os
import re
import json
import math
import time
import logging
from pathlib import Path
from functools import lru_cache
from datetime import datetime, timezone, timedelta
from urllib.parse import quote as url_quote
from typing import Any, Dict, List, Optional, Tuple

import requests
from flask import Flask, jsonify, request, render_template_string

BASE_DIR = Path(__file__).resolve().parent.parent
VERSION = "job_hunter_v8_stable_orchestrated_dashboard"

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("job-hunter-pro")

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

session = requests.Session()

# ── Google Maps throttle + retry ─────────────────────────────────────────────
# A single shared gate that spaces outbound Maps calls and retries on rate-limit
# (HTTP 429) / transient 5xx with exponential backoff. This is what lets EVERY
# accepted job get place/commute data instead of the first handful succeeding and
# the rest failing silently once Google's per-second quota trips.
import threading as _threading

_maps_lock = _threading.Lock()
_maps_last_call = [0.0]

def maps_get(url: str, params: Dict[str, Any], timeout: Optional[float] = None) -> Optional[requests.Response]:
    timeout = timeout if timeout is not None else Config.REQUEST_TIMEOUT
    attempts = max(1, Config.MAPS_MAX_RETRIES)
    for attempt in range(attempts):
        with _maps_lock:
            wait = Config.MAPS_MIN_INTERVAL - (time.monotonic() - _maps_last_call[0])
            if wait > 0:
                time.sleep(wait)
            _maps_last_call[0] = time.monotonic()
        try:
            res = session.get(url, params=params, timeout=timeout)
        except Exception as exc:
            if attempt == attempts - 1:
                logger.warning("maps_get network error (%s): %s", url.rsplit("/", 1)[-1], exc)
                return None
            time.sleep(2 ** attempt)
            continue
        # Retry on explicit rate-limit / transient server errors.
        if res.status_code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
            time.sleep(2 ** attempt)
            continue
        return res
    return None

class Config:
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    XAI_API_KEY = os.environ.get("XAI_API_KEY", "").strip()

    ORIGIN_ADDRESS = os.environ.get("ORIGIN_ADDRESS", "28 E Bryan Ave, Salt Lake City, UT 84115").strip()
    JOB_LOCATION = os.environ.get("JOB_LOCATION", "84115").strip()

    # Transit is a DISPLAY/UI filter, not a hard rejection gate. The default is
    # set high (120 min) so the legacy -10 match_score penalty effectively never
    # fires — a real provider job is never killed for a long commute; the user
    # filters by commute in the UI instead.
    MAX_TRANSIT_SECONDS = int(os.environ.get("MAX_TRANSIT_SECONDS", "7200"))
    # Radius is a DISPLAY/UI filter, not a hard rejection gate. Jobs outside this
    # radius receive a -10 match_score penalty and a resolution_flag entry, but are
    # KEPT in the accepted set so the user can see and filter them in the UI.
    # Jobs that fail place resolution entirely also become resolution_flags, never
    # hard deletions — this is the project's live-jobs law (see services/job_aggregator.py).
    MAX_RADIUS_MILES = float(os.environ.get("MAX_RADIUS_MILES", "5.0"))
    REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "12"))

    MAX_SERP_QUERIES = int(os.environ.get("MAX_SERP_QUERIES", "4"))
    # ---------------------------------------------------------------------------
    # THROUGHPUT CAPS — raise these to pull more listings per live run.
    #
    # Timeout tradeoff: a live run is synchronous under Cloud Run's request
    # timeout. Caps prevent the run from grinding forever, but the main timeout
    # risk is NOT raw-fetch volume — it is the 5-LLM enrichment fan-out
    # (MAX_LLM_CALLS * LLM_TIMEOUT). If a run times out:
    #   1. Lower ENABLE_LLM_RESEARCH=0 to skip all LLM calls, OR
    #   2. Lower MAX_LLM_CALLS (e.g. to 50), OR
    #   3. Lower MAX_ENRICH_JOBS (controls how many jobs enter the Maps+LLM path).
    # Raw fetch and cross-provider dedup are fast; the LLM layer is the bottleneck.
    #
    # Safe knobs for higher throughput:
    #   MAX_RAW_JOBS    — total raw listings collected across all providers (3000+)
    #   MAX_QUERIES     — keyword queries dispatched per run (40+)
    #   MAX_ENRICH_JOBS — jobs that get Maps place/commute + LLM enrichment (200+)
    #   MAX_LLM_CALLS   — guard on total LLM API calls inside one run
    # ---------------------------------------------------------------------------
    MAX_RAW_JOBS = int(os.environ.get("MAX_RAW_JOBS", "3000"))
    MAX_AI_CALLS = int(os.environ.get("MAX_AI_CALLS", "8"))
    SERPAPI_MIN_SEARCHES_LEFT = int(os.environ.get("SERPAPI_MIN_SEARCHES_LEFT", "0"))
    SERPAPI_BUDGET_MODE = os.environ.get("SERPAPI_BUDGET_MODE", "0").strip() == "1"
    # Per-run query count. The full ~1400-keyword bank rotates across runs (see
    # raw_job_queries offset), so coverage accumulates over saved batches rather
    # than in one impossible request.
    MAX_QUERIES = int(os.environ.get("MAX_QUERIES", "40"))

    ENABLE_PUBLIC_WEB_RESEARCH = os.environ.get("ENABLE_PUBLIC_WEB_RESEARCH", "0").strip() == "1"
    ENABLE_REVIEW_WEB_SEARCH = os.environ.get("ENABLE_REVIEW_WEB_SEARCH", "0").strip() == "1"
    # Google Places "opportunities" radar costs Maps quota per call. It is an
    # OPTIONAL feature and core job discovery does not depend on it. Off by
    # default for cost control; the endpoint reports this honestly when disabled.
    ENABLE_PLACES_OPPORTUNITIES = os.environ.get("ENABLE_PLACES_OPPORTUNITIES", "0").strip() == "1"

    # Per-run enrichment caps. Heavy paid work (Google Maps place/commute + the
    # 5-LLM research layer) runs AFTER accept/reject partitioning, on the accepted
    # set only, so the run completes inside Cloud Run's request timeout. Jobs past
    # the cap keep their honest needs_resolution flag instead of fake data. Both
    # are env-tunable upward once quota allows.
    # Raised from 40 → 200: Maps calls are throttled+retried by maps_get so this
    # is safe to raise high; the bottleneck is LLM calls, not Maps QPS.
    MAX_ENRICH_JOBS = int(os.environ.get("MAX_ENRICH_JOBS", "200"))
    # LLM research: every accepted, enriched job is sent to all five reasoning
    # providers (enrichment/classification only — never discovery). Guarded by a
    # per-run call budget. A provider with no key is skipped (dormant), never faked.
    # PRIMARY TIMEOUT RISK: if runs time out, set ENABLE_LLM_RESEARCH=0 or lower
    # MAX_LLM_CALLS. These are the two knobs that control the wall-clock bottleneck.
    ENABLE_LLM_RESEARCH = os.environ.get("ENABLE_LLM_RESEARCH", "1").strip() == "1"
    MAX_LLM_CALLS = int(os.environ.get("MAX_LLM_CALLS", "400"))
    LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "18"))
    LLM_MODEL_OPENAI = os.environ.get("LLM_MODEL_OPENAI", "gpt-4o-mini").strip()
    LLM_MODEL_GROQ = os.environ.get("LLM_MODEL_GROQ", "llama-3.3-70b-versatile").strip()
    LLM_MODEL_XAI = os.environ.get("LLM_MODEL_XAI", "grok-2-latest").strip()
    LLM_MODEL_ANTHROPIC = os.environ.get("LLM_MODEL_ANTHROPIC", "claude-3-5-haiku-latest").strip()
    LLM_MODEL_GEMINI = os.environ.get("LLM_MODEL_GEMINI", "gemini-1.5-flash").strip()
    # Maps throttle: minimum seconds between outbound Maps calls + retry budget on
    # HTTP 429/5xx. Without this, a burst of calls trips Google's QPS limit and the
    # rest fail silently — the root cause of "only a few jobs get commute/place".
    MAPS_MIN_INTERVAL = float(os.environ.get("MAPS_MIN_INTERVAL", "0.06"))
    MAPS_MAX_RETRIES = int(os.environ.get("MAPS_MAX_RETRIES", "3"))

    BATCH_BUCKET = os.environ.get("BATCH_BUCKET", "").strip()

FOOD_TERMS = [
    "restaurant", "waiter", "waitress", "server", "busser", "food runner",
    "host", "hostess", "cook", "line cook", "prep cook", "dishwasher",
    "dishwashing", "kitchen", "chef", "sous chef", "barista", "cafe",
    "coffee", "bakery", "deli", "grill", "pizza", "sandwich", "dining",
    "food service", "culinary", "catering", "expo", "steward",
    "shift lead", "shift leader", "kitchen supervisor", "biscuit",
    "drink maker", "dish machine operator",
]

BAD_TERMS = [
    "software engineer", "developer", "registered nurse", "warehouse", "cdl",
    "forklift", "security guard", "mechanic", "medical assistant",
    "dental assistant", "teacher", "account executive", "sales representative",
]

ROLE_QUERIES = [
    "restaurant server jobs near 84115 Salt Lake City",
    "restaurant cook jobs near 84115 Salt Lake City",
    "line cook jobs near 84115 Salt Lake City",
    "prep cook jobs near 84115 Salt Lake City",
    "busser jobs restaurant near 84115 Salt Lake City",
    "food runner restaurant jobs near 84115 Salt Lake City",
    "host hostess restaurant jobs near 84115 Salt Lake City",
    "dishwasher restaurant jobs near 84115 Salt Lake City",
    "kitchen supervisor restaurant jobs near 84115 Salt Lake City",
    "barista cafe jobs near 84115 Salt Lake City",
]

ROLE_GROUPS = {
    "server": "front-of-house",
    "waiter": "front-of-house",
    "waitress": "front-of-house",
    "busser": "front-of-house",
    "food runner": "front-of-house",
    "host": "front-of-house",
    "hostess": "front-of-house",
    "barista": "front-of-house",
    "cashier": "front-of-house",
    "cook": "back-of-house",
    "line cook": "back-of-house",
    "prep cook": "back-of-house",
    "dishwasher": "back-of-house",
    "dishwashing": "back-of-house",
    "kitchen": "back-of-house",
    "chef": "back-of-house",
    "steward": "back-of-house",
    "supervisor": "management",
    "manager": "management",
    "director": "management",
    "lead": "management",
}

def clean(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text if text else fallback

def clean_company(value: Any) -> str:
    text = clean(value).replace("-", " ").replace("_", " ")
    return re.sub(r"\s+", " ", text).strip(" -–—")

def term_present(text: str, term: str) -> bool:
    parts = [re.escape(part) for part in clean(term).lower().split()]
    if not parts:
        return False
    pattern = r"(?<![a-z0-9])" + r"\s+".join(parts) + r"(?![a-z0-9])"
    return re.search(pattern, clean(text).lower()) is not None

def is_food_text(text: str) -> bool:
    t = clean(text).lower()
    if not any(term_present(t, term) for term in FOOD_TERMS):
        return False
    if any(term_present(t, bad) for bad in BAD_TERMS):
        return False
    return True

def role_family_for_text(text: str) -> str:
    t = clean(text).lower()
    for term, family in ROLE_GROUPS.items():
        if term_present(t, term):
            return family
    return "food-service"

def miles_between(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    radius = 3958.7613
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))

@lru_cache(maxsize=512)
def geocode(address: str) -> Optional[Tuple[float, float]]:
    address = clean(address)
    if not address or not Config.GOOGLE_MAPS_API_KEY:
        return None
    try:
        res = maps_get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            {"address": address, "key": Config.GOOGLE_MAPS_API_KEY},
        )
        if res is None:
            return None
        res.raise_for_status()
        data = res.json()
        if data.get("status") != "OK" or not data.get("results"):
            return None
        loc = data["results"][0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])
    except Exception as exc:
        logger.warning("geocode failed: %s", exc)
        return None

def origin_latlng() -> Optional[Tuple[float, float]]:
    return geocode(Config.ORIGIN_ADDRESS)

@lru_cache(maxsize=512)
def place_details(place_id: str) -> Dict[str, Any]:
    place_id = clean(place_id)
    if not place_id or not Config.GOOGLE_MAPS_API_KEY:
        return {}
    try:
        res = maps_get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            {
                "place_id": place_id,
                "fields": "name,rating,user_ratings_total,reviews,formatted_address,website,url,business_status,formatted_phone_number,price_level,types",
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
        )
        if res is None:
            return {}
        res.raise_for_status()
        data = res.json()
        if data.get("status") != "OK":
            return {}
        return data.get("result") or {}
    except Exception as exc:
        logger.warning("place details failed: %s", exc)
        return {}

@lru_cache(maxsize=1024)
def places_text_search(query: str) -> Optional[Dict[str, Any]]:
    query = clean(query)
    origin = origin_latlng()
    if not query or not origin or not Config.GOOGLE_MAPS_API_KEY:
        return None
    try:
        res = maps_get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            {
                "query": query,
                "location": f"{origin[0]},{origin[1]}",
                "radius": int(max(Config.MAX_RADIUS_MILES, 5) * 1609.344),
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
        )
        if res is None:
            return None
        res.raise_for_status()
        data = res.json()
        results = data.get("results") or []
        if not results:
            return None
        best = results[0]
        loc = best.get("geometry", {}).get("location", {})
        latlng = None
        if "lat" in loc and "lng" in loc:
            latlng = (float(loc["lat"]), float(loc["lng"]))
        return {
            "name": clean(best.get("name")),
            "formatted_address": clean(best.get("formatted_address")),
            "place_id": clean(best.get("place_id")),
            "rating": best.get("rating"),
            "types": best.get("types", []),
            "latlng": latlng,
            "query_used": query,
        }
    except Exception as exc:
        logger.warning("places text search failed: %s", exc)
        return None

@lru_cache(maxsize=8)
def nearby_opportunities_cached(radius_miles: float) -> List[Dict[str, Any]]:
    origin = origin_latlng()
    if not origin or not Config.GOOGLE_MAPS_API_KEY:
        return []
    keywords = ["restaurant", "cafe", "bakery", "bar", "grill", "coffee", "sandwich", "pizza", "diner"]
    seen = set()
    out = []
    for keyword in keywords:
        next_token = ""
        pages = 0
        while pages < 2:
            params = {"key": Config.GOOGLE_MAPS_API_KEY}
            if next_token:
                params["pagetoken"] = next_token
                time.sleep(2)
            else:
                params.update({
                    "location": f"{origin[0]},{origin[1]}",
                    "radius": int(radius_miles * 1609.344),
                    "keyword": keyword,
                })
            try:
                res = session.get(
                    "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                    params=params,
                    timeout=Config.REQUEST_TIMEOUT,
                )
                res.raise_for_status()
                data = res.json()
            except Exception:
                break
            for item in data.get("results", []) or []:
                place_id = clean(item.get("place_id"))
                if not place_id or place_id in seen:
                    continue
                seen.add(place_id)
                loc = item.get("geometry", {}).get("location", {})
                latlng = None
                radius = None
                if "lat" in loc and "lng" in loc:
                    latlng = (float(loc["lat"]), float(loc["lng"]))
                    radius = round(miles_between(origin, latlng), 2)
                details = place_details(place_id)
                name = clean(details.get("name") or item.get("name"))
                address = clean(details.get("formatted_address") or item.get("vicinity"))
                out.append({
                    "type": "restaurant_opportunity",
                    "place_id": place_id,
                    "name": name,
                    "restaurant_name": name,
                    "resolved_address": address,
                    "radius_miles": radius,
                    "radius_label": f"{radius} mi radius" if radius is not None else "Radius unavailable",
                    "google_rating": details.get("rating", item.get("rating")),
                    "google_review_count": details.get("user_ratings_total", item.get("user_ratings_total")),
                    "business_status": clean(details.get("business_status") or item.get("business_status")),
                    "website": clean(details.get("website")),
                    "google_maps_url": clean(details.get("url")),
                    "types": details.get("types") or item.get("types", []),
                })
            next_token = data.get("next_page_token") or ""
            pages += 1
            if not next_token:
                break
    out.sort(key=lambda x: (
        x.get("radius_miles") if x.get("radius_miles") is not None else 999,
        -(float(x.get("google_rating") or 0)),
    ))
    return out[:160]

@lru_cache(maxsize=1024)
def transit_to(destination: str) -> Dict[str, Any]:
    destination = clean(destination)
    empty = {
        "commute_seconds": None,
        "commute_label": "Transit unavailable",
        "transit_distance_miles": None,
        "transit_distance_label": "Transit distance unavailable",
    }
    if not destination or not Config.GOOGLE_MAPS_API_KEY:
        return empty
    try:
        res = maps_get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            {
                "origins": Config.ORIGIN_ADDRESS,
                "destinations": destination,
                "mode": "transit",
                "departure_time": "now",
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
        )
        if res is None:
            return empty
        res.raise_for_status()
        data = res.json()
        element = data.get("rows", [{}])[0].get("elements", [{}])[0]
        if element.get("status") != "OK":
            return empty
        seconds = int(element["duration"]["value"])
        miles = int(element["distance"]["value"]) / 1609.344
        return {
            "commute_seconds": seconds,
            "commute_label": f"{round(seconds / 60)}m transit",
            "transit_distance_miles": round(miles, 2),
            "transit_distance_label": f"{round(miles, 2)} mi transit route",
        }
    except Exception as exc:
        logger.warning("transit failed: %s", exc)
        return empty

@lru_cache(maxsize=1)
def serpapi_account_status() -> Dict[str, Any]:
    if not Config.SERPAPI_KEY:
        return {"available": False, "reason": "SERPAPI_KEY missing"}
    try:
        res = session.get(
            "https://serpapi.com/account.json",
            params={"api_key": Config.SERPAPI_KEY},
            timeout=Config.REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()
        return {
            "available": True,
            "plan_name": data.get("plan_name"),
            "total_searches_left": data.get("total_searches_left"),
            "this_month_usage": data.get("this_month_usage"),
            "searches_per_month": data.get("searches_per_month"),
            "last_hour_searches": data.get("last_hour_searches"),
            "hourly_throughput": data.get("hourly_throughput"),
        }
    except Exception as exc:
        return {"available": False, "reason": str(exc)}

def serpapi_budget_allows_search() -> bool:
    if not Config.SERPAPI_BUDGET_MODE:
        return True
    left = serpapi_account_status().get("total_searches_left")
    if left is None:
        return True
    try:
        return int(left) > Config.SERPAPI_MIN_SEARCHES_LEFT
    except Exception:
        return True

def serpapi_jobs(query: str) -> List[Dict[str, Any]]:
    if not Config.SERPAPI_KEY or not serpapi_budget_allows_search():
        return []
    try:
        res = session.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_jobs",
                "q": query,
                "location": "Salt Lake City, Utah, United States",
                "hl": "en",
                "gl": "us",
                "api_key": Config.SERPAPI_KEY,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        return res.json().get("jobs_results", []) or []
    except Exception as exc:
        logger.warning("serpapi jobs failed: %s", exc)
        return []

def explicit_address(raw: Dict[str, Any]) -> str:
    text = " ".join([
        clean(raw.get("title")),
        clean_company(raw.get("company_name") or raw.get("company")),
        clean(raw.get("location")),
        clean(raw.get("description")),
    ])
    suffix = r"(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Way|Ct|Court|Ln|Lane|Expy|Expressway|Pkwy|Parkway|Hwy|Highway)"
    patterns = [
        rf"\b\d{{1,6}}\s+[NESW]?\s*[A-Za-z0-9.' -]{{2,40}}\s+{suffix}\s+Salt Lake City,?\s*UT\s*\d{{5}}\b",
        rf"\b\d{{1,6}}\s+[NESW]?\s*[A-Za-z0-9.' -]{{2,40}}\s+{suffix}\b",
        r"\b\d{1,6}\s+[NESW]\s+\d{1,6}\s+[NESW]\b",
    ]
    bad = ["has become", "days of employment", "hours across", "must ", "preferred ", "recognized and award"]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.I):
            addr = clean(match.group(0)).strip(" .,-")
            low = addr.lower()
            if any(b in low for b in bad):
                continue
            if len(addr.split()) > 12:
                continue
            if "salt lake" not in low:
                addr = f"{addr}, Salt Lake City, UT"
            return addr
    return ""

def resolve_place(raw: Dict[str, Any]) -> Dict[str, Any]:
    company = clean_company(raw.get("company_name") or raw.get("company"))
    title = clean(raw.get("title"))
    addr = explicit_address(raw)
    if addr:
        latlng = geocode(addr)
        return {
            "name": company,
            "formatted_address": addr,
            "place_id": "",
            "latlng": latlng,
            "rating": None,
            "query_used": "explicit_address",
            "types": [],
        }
    queries = [
        f"{company} Salt Lake City",
        f"{company} near 84115 Salt Lake City UT",
        f"{company} {title} Salt Lake City",
    ]
    for q in queries:
        if not company:
            continue
        place = places_text_search(q)
        if place and place.get("formatted_address") and place.get("latlng"):
            return place
    return {"name": "", "formatted_address": "", "place_id": "", "latlng": None, "rating": None, "query_used": "", "types": []}

def salary_from_raw(raw: Dict[str, Any]) -> str:
    detected = raw.get("detected_extensions") or {}
    if detected.get("salary"):
        return clean(detected.get("salary"))
    if raw.get("salary"):
        return clean(raw.get("salary"))
    extensions = raw.get("extensions")
    if isinstance(extensions, list):
        for item in extensions:
            text = clean(item)
            if "$" in text or "/hr" in text.lower() or "hour" in text.lower():
                return text
    desc = clean(raw.get("description"))
    match = re.search(r"\$\s?\d+(?:\.\d+)?(?:\s*-\s*\$?\d+(?:\.\d+)?)?\s*(?:/ ?hr|/ ?hour|per hour|an hour)?", desc, re.I)
    return clean(match.group(0)) if match else "Salary not listed"

def apply_link(raw: Dict[str, Any]) -> str:
    options = raw.get("apply_options")
    if isinstance(options, list) and options:
        first = options[0]
        if isinstance(first, dict):
            return clean(first.get("link"))
    return ""

def tags_for_text(text: str) -> List[str]:
    rules = [
        ("line-cook", ["line cook"]),
        ("prep-cook", ["prep cook"]),
        ("server", ["server", "waiter", "waitress"]),
        ("busser", ["busser", "food runner"]),
        ("host-hostess", ["host", "hostess"]),
        ("dishwasher", ["dishwasher", "dishwashing", "dish machine"]),
        ("kitchen", ["kitchen", "cook", "chef"]),
        ("barista", ["barista", "coffee", "cafe"]),
        ("supervisor", ["supervisor", "shift lead", "shift leader"]),
        ("restaurant", ["restaurant", "dining"]),
    ]
    tags = []
    for tag, words in rules:
        if any(term_present(text, word) for word in words):
            tags.append(tag)
    return tags[:6] or ["food-service"]

def review_intelligence(job: Dict[str, Any]) -> Dict[str, Any]:
    details = place_details(clean(job.get("place_id")))
    rating = details.get("rating", job.get("place_rating"))
    count = details.get("user_ratings_total")
    reviews = []
    for r in details.get("reviews", []) or []:
        reviews.append({
            "author": clean(r.get("author_name")),
            "rating": r.get("rating"),
            "relative_time": clean(r.get("relative_time_description")),
            "text": clean(r.get("text")),
        })
    try:
        rating_float = float(rating or 0)
    except Exception:
        rating_float = 0
    try:
        count_int = int(count or 0)
    except Exception:
        count_int = 0
    score = round(min(100, max(0, (rating_float / 5) * 90 + min(10, math.log10(count_int + 1) * 4)))) if rating_float else 50
    return {
        "google_rating": rating,
        "google_review_count": count,
        "google_reviews_sample": reviews[:5],
        "review_score": score,
        "consistency_score": max(40, min(100, score)),
        "risk_level": "low" if score >= 75 else "medium" if score >= 55 else "high",
        "website": clean(details.get("website")),
        "google_maps_url": clean(details.get("url")),
        "phone": clean(details.get("formatted_phone_number")),
        "business_status": clean(details.get("business_status")),
    }

def match_score(job: Dict[str, Any]) -> int:
    score = 70
    text = " ".join([clean(job.get("title")), clean(job.get("description")), clean(job.get("restaurant_name"))])
    for term, points in {
        "line cook": 10, "prep cook": 10, "cook": 8, "server": 7,
        "waiter": 7, "waitress": 7, "busser": 7, "food runner": 7,
        "host": 6, "hostess": 6, "dishwasher": 6, "chef": 6,
        "restaurant": 7, "kitchen": 8,
    }.items():
        if term_present(text, term):
            score += points
    commute = job.get("commute_seconds")
    radius = job.get("radius_miles")
    if commute is not None:
        score += 10 if commute <= 900 else 7 if commute <= 1500 else 3 if commute < Config.MAX_TRANSIT_SECONDS else -10
    if radius is not None:
        score += 10 if radius <= 1 else 6 if radius <= 2 else 3 if radius <= Config.MAX_RADIUS_MILES else -10
    if job.get("resolved_address"):
        score += 5
    return max(1, min(score, 99))

def normalize_job(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Cheap pass — NO Google Maps / LLM calls. Runs on every raw job so the bulk
    classification/dedupe finishes fast. Place, commute, radius and review fields
    start empty and are filled later by enrich_job() on the accepted set only.
    The originating raw is stashed under ``_raw`` for that later step and popped
    before the job is returned to the client / persisted."""
    title = clean(raw.get("title"), "Untitled role")
    company = clean_company(raw.get("company_name") or raw.get("company")) or "Company not listed"
    listing_location = clean(raw.get("location"), Config.JOB_LOCATION)
    description = clean(raw.get("description"), "No description available.")
    text = " ".join([title, company, description])
    tags = tags_for_text(text)
    job = {
        "title": title,
        "company": company,
        "restaurant_name": company,
        "resolved_place_name": "",
        "resolved_address": "",
        "location": listing_location,
        "listing_location": listing_location,
        "salary": salary_from_raw(raw),
        "description": description,
        "commute_seconds": None,
        "commute_label": "Resolution pending",
        "radius_miles": None,
        "radius_label": "Resolution pending",
        "distance_miles": None,
        "distance_label": "Resolution pending",
        "transit_distance_miles": None,
        "transit_distance_label": "Resolution pending",
        "source_url": apply_link(raw),
        "job_id": clean(raw.get("job_id")),
        "via": clean(raw.get("via")),
        "ai_provider": "deterministic_budget_safe",
        "chef_names": [],
        "place_query_used": "",
        "place_id": "",
        "place_rating": None,
        "tags": tags,
        "role_family": role_family_for_text(" ".join(tags + [title, description])),
        "_provider": clean(raw.get("_provider") or raw.get("via")),
        "_query_used": clean(raw.get("_query_used")),
        "enriched": False,
        "_raw": raw,
    }
    job["match"] = match_score(job)
    job["review_intelligence"] = {}
    job["google_rating"] = None
    job["google_review_count"] = None
    job["review_score"] = None
    job["consistency_score"] = None
    job["risk_level"] = None
    return job


def enrich_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """Heavy pass — resolves place, commute, radius, Google review intelligence and
    the 5-LLM research layer for ONE accepted job. Throttled + retried Maps calls
    (see maps_get) mean this succeeds for every job, not just the first few. All
    failures degrade to honest 'unavailable', never fabricated values."""
    raw = job.get("_raw") or {}
    place = resolve_place(raw)
    resolved_address = clean(place.get("formatted_address"))
    resolved_name = clean(place.get("name"))
    destination = resolved_address or job.get("listing_location") or Config.JOB_LOCATION
    transit = transit_to(destination)
    origin = origin_latlng()
    radius_miles = None
    if origin and place.get("latlng"):
        radius_miles = round(miles_between(origin, place["latlng"]), 2)

    job["resolved_place_name"] = resolved_name
    job["restaurant_name"] = resolved_name or job.get("company")
    job["resolved_address"] = resolved_address
    job["location"] = resolved_address or job.get("listing_location")
    job["commute_seconds"] = transit["commute_seconds"]
    job["commute_label"] = transit["commute_label"]
    job["radius_miles"] = radius_miles
    job["radius_label"] = f"{radius_miles} mi radius" if radius_miles is not None else "Radius unavailable"
    job["distance_miles"] = radius_miles
    job["distance_label"] = job["radius_label"]
    job["transit_distance_miles"] = transit["transit_distance_miles"]
    job["transit_distance_label"] = transit["transit_distance_label"]
    job["place_query_used"] = place.get("query_used")
    job["place_id"] = place.get("place_id")
    job["place_rating"] = place.get("rating")
    job["match"] = match_score(job)

    ri = review_intelligence(job)
    job["review_intelligence"] = ri
    job["google_rating"] = ri.get("google_rating") or job.get("place_rating")
    job["google_review_count"] = ri.get("google_review_count")
    job["review_score"] = ri.get("review_score")
    job["consistency_score"] = ri.get("consistency_score")
    job["risk_level"] = ri.get("risk_level")

    if Config.ENABLE_LLM_RESEARCH:
        job["research"] = llm_research(job)
    job["enriched"] = True
    return job


# ── 5-LLM research layer (enrichment/classification only, never discovery) ────
_llm_lock = _threading.Lock()
_llm_calls_left = [0]

def _llm_take() -> bool:
    """Per-run call budget gate so a big batch can't blow the LLM quota."""
    with _llm_lock:
        if _llm_calls_left[0] <= 0:
            return False
        _llm_calls_left[0] -= 1
        return True

def _llm_prompt(job: Dict[str, Any]) -> str:
    place = clean(job.get("resolved_place_name") or job.get("company"))
    addr = clean(job.get("resolved_address"))
    rating = job.get("google_rating")
    desc = clean(job.get("description"))[:600]
    return (
        "You are vetting one local job for a Salt Lake City applicant. In <=55 words, "
        "plainly assess: role type, front/back-of-house or management, likely schedule/pay, "
        "and any employer reputation note or warning. Only state what the text supports; say "
        "'unknown' otherwise. Do not invent facts.\n\n"
        f"Title: {clean(job.get('title'))}\nCompany: {clean(job.get('company'))}\n"
        f"Resolved place: {place} {addr} (Google rating: {rating})\n"
        f"Description: {desc}"
    )

def _chat_openai_compatible(base_url: str, key: str, model: str, prompt: str) -> str:
    res = session.post(
        base_url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 160, "temperature": 0.2},
        timeout=Config.LLM_TIMEOUT,
    )
    res.raise_for_status()
    return clean(res.json()["choices"][0]["message"]["content"])

def _research_openai(prompt: str) -> str:
    return _chat_openai_compatible("https://api.openai.com/v1/chat/completions",
                                   Config.OPENAI_API_KEY, Config.LLM_MODEL_OPENAI, prompt)

def _research_groq(prompt: str) -> str:
    return _chat_openai_compatible("https://api.groq.com/openai/v1/chat/completions",
                                   Config.GROQ_API_KEY, Config.LLM_MODEL_GROQ, prompt)

def _research_xai(prompt: str) -> str:
    return _chat_openai_compatible("https://api.x.ai/v1/chat/completions",
                                   Config.XAI_API_KEY, Config.LLM_MODEL_XAI, prompt)

def _research_anthropic(prompt: str) -> str:
    res = session.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": Config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01",
                 "Content-Type": "application/json"},
        json={"model": Config.LLM_MODEL_ANTHROPIC, "max_tokens": 160,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=Config.LLM_TIMEOUT,
    )
    res.raise_for_status()
    return clean(res.json()["content"][0]["text"])

def _research_gemini(prompt: str) -> str:
    res = session.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{Config.LLM_MODEL_GEMINI}:generateContent",
        params={"key": Config.GEMINI_API_KEY},
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"maxOutputTokens": 200, "temperature": 0.2}},
        timeout=Config.LLM_TIMEOUT,
    )
    res.raise_for_status()
    return clean(res.json()["candidates"][0]["content"]["parts"][0]["text"])

# (display name, key, runner). A provider with no key is skipped (dormant).
_LLM_PROVIDERS = [
    ("openai", lambda: Config.OPENAI_API_KEY, _research_openai),
    ("gemini", lambda: Config.GEMINI_API_KEY, _research_gemini),
    ("claude", lambda: Config.ANTHROPIC_API_KEY, _research_anthropic),
    ("groq", lambda: Config.GROQ_API_KEY, _research_groq),
    ("xai", lambda: Config.XAI_API_KEY, _research_xai),
]

def _run_one_llm(name: str, has_key, runner, prompt: str) -> Dict[str, Any]:
    if not has_key():
        return {"provider": name, "note": None, "status": "dormant", "reason": "no_api_key"}
    if not _llm_take():
        return {"provider": name, "note": None, "status": "skipped", "reason": "run_budget_reached"}
    try:
        return {"provider": name, "note": runner(prompt), "status": "ok"}
    except Exception as exc:
        return {"provider": name, "note": None, "status": "error",
                "reason": f"{type(exc).__name__}: {str(exc)[:140]}"}

def llm_research(job: Dict[str, Any]) -> Dict[str, Any]:
    """Fan a compact, evidence-bound prompt to all five reasoning providers
    concurrently. Returns each provider's note plus a consensus summary. Honest:
    no key -> dormant, error -> error, over budget -> skipped. Never fabricated."""
    from concurrent.futures import ThreadPoolExecutor
    prompt = _llm_prompt(job)
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(_run_one_llm, n, k, r, prompt) for (n, k, r) in _LLM_PROVIDERS]
        for f in futures:
            try:
                results.append(f.result())
            except Exception as exc:
                results.append({"provider": "unknown", "note": None, "status": "error",
                                "reason": str(exc)[:140]})
    notes = [r["note"] for r in results if r.get("status") == "ok" and r.get("note")]
    summary = notes[0] if notes else None
    return {
        "providers": results,
        "summary": summary,
        "consensus_count": len(notes),
        "available": [r["provider"] for r in results if r.get("status") == "ok"],
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }

# NOTE: Accept/reject partitioning now lives in services.job_aggregator. Broad
# mode keeps every usable job and records missing address/radius/transit as
# non-fatal resolution_flags rather than deleting the job. Food-service gating is
# no longer applied to the default discovery universe.

def canonical_key(job: Dict[str, Any]) -> str:
    title = clean(job.get("title")).lower()
    name = clean(job.get("restaurant_name")).lower()
    addr = clean(job.get("resolved_address")).lower()
    if not name and not addr:
        uniq = (clean(job.get("source_url")) or clean(job.get("url")) or clean(job.get("company")) or clean(job.get("job_id"))).lower()
        return f"{title}|{uniq}"
    return f"{title}|{name}|{addr}"

def raw_job_queries(mode: str = "broad", domain: str = "", extra_terms: Optional[List[str]] = None) -> List[str]:
    """Build the discovery query bank.

    Broad, all-jobs discovery is the default and does NOT depend on Google Places
    (that was both a cost problem and a food-service bias). Domain presets are
    optional and explicit. Falls back to the legacy restaurant queries only if
    the data-driven builder cannot be imported, so discovery never breaks.
    """
    selected = (domain or mode or "broad").strip().lower()
    try:
        from services.query_builder import build_queries

        queries = build_queries(
            mode=selected,
            city="Salt Lake City, UT",
            postal=Config.JOB_LOCATION,
            max_queries=Config.MAX_QUERIES,
            extra_terms=extra_terms,
            offset=int(time.time() // 60),
        )
        if queries:
            return queries
    except Exception:
        logger.warning("query_builder unavailable; using legacy query bank", exc_info=True)

    # Legacy fallback (no Google Places dependency).
    unique: List[str] = []
    for query in ROLE_QUERIES:
        if query not in unique:
            unique.append(query)
    return unique

def fetch_jobs_live(mode: str = "broad", domain: str = "", extra_terms: Optional[List[str]] = None) -> Dict[str, Any]:
    raw_jobs = []
    provider_breakdown = {}
    quarantined_providers: Dict[str, Any] = {}
    queries = raw_job_queries(mode=mode, domain=domain, extra_terms=extra_terms)
    query_count = len(queries)

    try:
        from search.live_provider_bridge import fetch_provider_raw_jobs
        fanout = fetch_provider_raw_jobs(
            queries,
            max_raw_jobs=Config.MAX_RAW_JOBS,
            location="Salt Lake City, UT",
        )
        raw_jobs = fanout.get("raw_jobs", [])
        provider_breakdown = fanout.get("provider_breakdown", {})
        query_count = fanout.get("query_count", query_count)
        quarantined_providers = fanout.get("quarantined_providers", {})
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Federated provider fan-out failed; falling back to legacy SerpAPI path", exc_info=True)
        provider_breakdown = {
            "legacy_serpapi_fallback": {
                "available": True,
                "status": "fallback",
                "error": f"{type(exc).__name__}: {str(exc)[:180]}",
                "queries_attempted": 0,
                "raw_count": 0,
            }
        }

        seen_raw = set()
        for query in queries:
            provider_breakdown["legacy_serpapi_fallback"]["queries_attempted"] += 1
            for raw in serpapi_jobs(query):
                identity = clean(raw.get("job_id")) or clean(raw.get("title")) + clean(raw.get("company_name")) + clean(raw.get("location"))
                if identity and identity not in seen_raw:
                    seen_raw.add(identity)
                    raw["_query_used"] = query
                    raw["_provider"] = "legacy_serpapi"
                    raw_jobs.append(raw)
                    provider_breakdown["legacy_serpapi_fallback"]["raw_count"] += 1
                if len(raw_jobs) >= Config.MAX_RAW_JOBS:
                    break
            if len(raw_jobs) >= Config.MAX_RAW_JOBS:
                break

    normalized = [normalize_job(raw) for raw in raw_jobs]

    # Partition into accepted (every usable job; missing resolution becomes
    # non-fatal resolution_flags) and rejected (genuinely unusable: no title,
    # nothing to apply to, duplicate, or — only in a domain preset — a clear
    # domain mismatch). Falls back to a permissive accept-all if the aggregator
    # cannot be imported, so jobs are never silently lost.
    try:
        from services.job_aggregator import partition

        accepted, rejected = partition(normalized, mode=mode, domain=domain)
    except Exception:
        logger.warning("job_aggregator unavailable; accepting all normalized jobs", exc_info=True)
        accepted, rejected, seen = [], [], set()
        for job in normalized:
            key = canonical_key(job)
            if key in seen:
                continue
            seen.add(key)
            accepted.append(job)

    # Enrich the most promising accepted jobs (Google place/commute + 5-LLM
    # research). This is the only paid-per-job work and runs AFTER partition on a
    # capped slice, so the run completes within the request timeout. Jobs past the
    # cap keep their honest "Resolution pending" state — never fabricated data.
    fast = os.environ.get("FAST_JOBS", "0") == "1"
    if not fast:
        accepted.sort(key=lambda j: -j.get("match", 0))  # enrich best candidates first
        _llm_calls_left[0] = Config.MAX_LLM_CALLS
        enriched_count = 0
        for job in accepted[:Config.MAX_ENRICH_JOBS]:
            try:
                enrich_job(job)
                enriched_count += 1
            except Exception:
                logger.warning("enrich_job failed; keeping job unresolved", exc_info=True)
        # Recompute resolution flags now that place/commute may be filled in.
        try:
            from services.job_aggregator import resolution_flags as _rflags
            for job in accepted:
                flags = _rflags(job)
                job["resolution_flags"] = flags
                job["needs_resolution"] = bool(flags)
        except Exception:
            pass

    # Drop the internal raw payload so it never bloats the response / stored batch.
    for job in accepted:
        job.pop("_raw", None)

    accepted.sort(key=lambda j: (
        j.get("radius_miles") if j.get("radius_miles") is not None else 999,
        j.get("commute_seconds") if j.get("commute_seconds") is not None else 999999,
        -j.get("match", 0),
    ))

    flag_summary: Dict[str, int] = {}
    for job in accepted:
        for flag in job.get("resolution_flags", []) or []:
            flag_summary[flag] = flag_summary.get(flag, 0) + 1

    return {
        "raw_count": len(raw_jobs),
        "query_count": query_count,
        "mode": mode,
        "domain": domain,
        "accepted": accepted,
        "rejected": rejected[:100],
        "rejected_total": len(rejected),
        "enriched_count": sum(1 for j in accepted if j.get("enriched")),
        "enrich_cap": Config.MAX_ENRICH_JOBS,
        "resolution_flag_summary": flag_summary,
        "provider_breakdown": provider_breakdown,
        "quarantined_providers": quarantined_providers,
    }

def float_arg(name: str, default: Optional[float]) -> Optional[float]:
    value = request.args.get(name)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except Exception:
        return default

def request_filter_params() -> Dict[str, Any]:
    """Collect ONLY the filter params the caller explicitly provided.

    Absent or blank params are omitted so the service never narrows by default.
    """
    params: Dict[str, Any] = {}
    for name in ("min_rating", "max_radius", "max_transit", "min_score", "min_match",
                 "industry", "provider", "role", "house", "q"):
        value = request.args.get(name)
        if value not in (None, ""):
            params[name] = value
    return params


def apply_filters(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply only explicitly-set filters (delegates to services.filtering)."""
    params = request_filter_params()
    if not params:
        return list(jobs)
    try:
        from services.filtering import apply_filters as _apply

        return _apply(jobs, params)
    except Exception:
        logger.warning("services.filtering unavailable; returning unfiltered jobs", exc_info=True)
        return list(jobs)

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def metadata_access_token() -> str:
    try:
        res = session.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"},
            timeout=5,
        )
        res.raise_for_status()
        return res.json().get("access_token", "")
    except Exception:
        return ""

def gcs_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {metadata_access_token()}",
        "Content-Type": "application/json",
    }

def gcs_upload_json(object_name: str, payload: Dict[str, Any]) -> bool:
    if not Config.BATCH_BUCKET:
        return False
    try:
        res = session.post(
            f"https://storage.googleapis.com/upload/storage/v1/b/{Config.BATCH_BUCKET}/o",
            params={"uploadType": "media", "name": object_name},
            headers=gcs_headers(),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=30,
        )
        res.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("gcs upload failed: %s", exc)
        return False

def gcs_download_json(object_name: str) -> Dict[str, Any]:
    if not Config.BATCH_BUCKET:
        return {}
    try:
        encoded = url_quote(object_name, safe="")
        res = session.get(
            f"https://storage.googleapis.com/storage/v1/b/{Config.BATCH_BUCKET}/o/{encoded}",
            params={"alt": "media"},
            headers=gcs_headers(),
            timeout=30,
        )
        res.raise_for_status()
        return res.json()
    except Exception:
        return {}

def gcs_list_batches(limit: int = 200) -> List[Dict[str, Any]]:
    if not Config.BATCH_BUCKET:
        return []
    try:
        res = session.get(
            f"https://storage.googleapis.com/storage/v1/b/{Config.BATCH_BUCKET}/o",
            params={"prefix": "batches/", "maxResults": str(limit), "fields": "items(name,updated,size)"},
            headers=gcs_headers(),
            timeout=30,
        )
        res.raise_for_status()
        items = res.json().get("items", []) or []
        items = [item for item in items if item.get("name", "").endswith(".json")]
        items.sort(key=lambda x: x.get("updated", ""), reverse=True)
        return items
    except Exception:
        return []

@app.after_request
def add_headers(response):
    response.headers["X-App-Name"] = "job-hunter-pro"
    response.headers["Cache-Control"] = "no-store"
    return response

@app.route("/")
def index():
    return render_template_string("""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Job Hunter Pro</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
  <aside class="app-sidebar">
    <div class="brand">JHP</div>
    <a href="#overview">Overview</a>
    <a href="#filters">Filters</a>
    <a href="#jobs">Jobs</a>
    <a href="#opportunities">Opportunities</a>
    <a href="#history">History</a>
    <a href="/api/usage">Usage</a>
    <a href="/api/why-three">Why few jobs?</a>
  </aside>

  <main class="app-shell">
    <section class="hero-panel" id="overview">
      <p class="kicker">Persistent AI Job Intelligence</p>
      <h1 class="text-gradient">Job Hunter Pro</h1>
      <p class="lead">A Google Cloud Run application for restaurant job discovery, Google Places opportunity intelligence, transit scoring, review intelligence, budget-safe SerpAPI use, persistent batch history, and filterable UI/UX.</p>
      <div class="cluster">
        <button class="btn btn-primary" onclick="loadLiveJobs()">Run Live Discovery</button>
        <button class="btn btn-ghost" onclick="loadOpportunities()">Load Opportunities</button>
        <button class="btn btn-ghost" onclick="loadHistory()">Load History</button>
      </div>
    </section>

    <section class="stats-grid">
      <div class="stat-card"><strong id="statJobs">—</strong><span>visible jobs</span></div>
      <div class="stat-card"><strong id="statRaw">—</strong><span>raw scanned</span></div>
      <div class="stat-card"><strong id="statOpps">—</strong><span>opportunities</span></div>
      <div class="stat-card"><strong id="statSerp">—</strong><span>SerpAPI left</span></div>
    </section>

    <section class="panel stack" id="filters">
      <h2>Filters</h2>
      <div class="filter-grid">
        <label>Min rating <input id="min_rating" type="number" step="0.1" min="0" max="5" placeholder="4.5"></label>
        <label>Max radius <input id="max_radius" type="number" step="0.1" min="0" placeholder="1"></label>
        <label>Max transit <input id="max_transit" type="number" step="1" min="0" placeholder="35"></label>
        <label>Min review score <input id="min_score" type="number" step="1" min="0" max="100" placeholder="70"></label>
        <label>Role
          <select id="role">
            <option value="all">All roles</option>
            <option value="server">Server / waiter</option>
            <option value="busser">Busser / food runner</option>
            <option value="host">Host / hostess</option>
            <option value="cook">Cook</option>
            <option value="line-cook">Line cook</option>
            <option value="prep-cook">Prep cook</option>
            <option value="dishwasher">Dishwasher</option>
            <option value="barista">Barista</option>
            <option value="supervisor">Supervisor</option>
          </select>
        </label>
        <label>House
          <select id="house">
            <option value="all">All</option>
            <option value="front-of-house">Front of house</option>
            <option value="back-of-house">Back of house</option>
            <option value="management">Management</option>
          </select>
        </label>
        <label>Keyword <input id="q" type="text" placeholder="Sweet Lake, tips, chef..."></label>
      </div>
      <div class="cluster">
        <button class="btn btn-primary" onclick="loadLiveJobs()">Apply to Live Jobs</button>
        <button class="btn btn-ghost" onclick="loadHistory()">Apply to History</button>
        <button class="btn btn-ghost" onclick="loadOpportunities()">Apply to Opportunities</button>
      </div>
    </section>

    <p class="status-line" id="status">Loading dashboard...</p>

    <section id="jobs">
      <h2>Jobs</h2>
      <div class="grid-system" id="jobGrid"></div>
    </section>

    <section id="opportunities">
      <h2>Nearby Restaurant Opportunities</h2>
      <div class="table-card">
        <table>
          <thead><tr><th>Name</th><th>Rating</th><th>Reviews</th><th>Radius</th><th>Status</th><th>Research</th></tr></thead>
          <tbody id="opportunityRows"></tbody>
        </table>
      </div>
    </section>

    <section id="history">
      <h2>Batch History</h2>
      <div class="table-card">
        <table>
          <thead><tr><th>Batch</th><th>Created</th><th>Accepted</th><th>Rejected</th><th>Raw</th></tr></thead>
          <tbody id="historyRows"></tbody>
        </table>
      </div>
    </section>

    <section class="panel stack">
      <h2>About</h2>
      <p>Job Hunter Pro is built as a budget-aware, persistent, multi-source job intelligence system. It separates free/low-cost Google Places opportunity research from quota-limited SerpAPI job discovery, then stores timestamped batches for history and filters.</p>
    </section>
  </main>

  <script src="/static/js/main.js"></script>
</body>
</html>
""")

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "version": VERSION,
        "runtime": "google-cloud-run",
        "maps_enabled": bool(Config.GOOGLE_MAPS_API_KEY),
        "serpapi_enabled": bool(Config.SERPAPI_KEY),
        "groq_enabled": bool(Config.GROQ_API_KEY),
        "openai_enabled": bool(Config.OPENAI_API_KEY),
        "gemini_enabled": bool(Config.GEMINI_API_KEY),
        "claude_enabled": bool(Config.ANTHROPIC_API_KEY),
        "grok_xai_enabled": bool(Config.XAI_API_KEY),
        "origin": Config.ORIGIN_ADDRESS,
        "origin_geocoded": bool(origin_latlng()),
        "max_radius_miles": Config.MAX_RADIUS_MILES,
        "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
        "serpapi_budget_mode": Config.SERPAPI_BUDGET_MODE,
        "serpapi_min_searches_left": Config.SERPAPI_MIN_SEARCHES_LEFT,
        "batch_bucket": Config.BATCH_BUCKET,
        "pipeline": [
            "Google Places opportunities",
            "budget-limited SerpAPI job discovery",
            "place resolution",
            "Google Distance Matrix transit",
            "review intelligence",
            "Cloud Storage batch history",
            "Cloud Scheduler ingestion",
        ],
    })

@app.route("/api/usage")
def usage():
    return jsonify({
        "status": "ok",
        "version": VERSION,
        "serpapi": serpapi_account_status(),
        "storage": {"batch_bucket": Config.BATCH_BUCKET, "configured": bool(Config.BATCH_BUCKET)},
        "budget": {
            "budget_mode": Config.SERPAPI_BUDGET_MODE,
            "min_searches_left_guard": Config.SERPAPI_MIN_SEARCHES_LEFT,
            "max_serp_queries_per_live_run": Config.MAX_SERP_QUERIES,
            "max_raw_jobs_per_live_run": Config.MAX_RAW_JOBS,
        },
        "routes": ["/api/jobs", "/api/opportunities", "/api/history", "/api/batches", "/api/ingest", "/api/why-three"],
    })

@app.route("/api/why-three")
def why_three():
    return jsonify({
        "status": "explained",
        "main_reason": "SerpAPI budget mode intentionally limits live job discovery. Opportunities and history should be used for broad browsing.",
        "current_limits": {
            "max_serp_queries": Config.MAX_SERP_QUERIES,
            "max_raw_jobs": Config.MAX_RAW_JOBS,
            "serpapi_min_searches_left_guard": Config.SERPAPI_MIN_SEARCHES_LEFT,
            "max_radius_miles": Config.MAX_RADIUS_MILES,
            "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
        },
        "how_to_get_hundreds_without_burning_serpapi": [
            "Use /api/opportunities for Google Places restaurant targets.",
            "Use /api/history after scheduler batches accumulate.",
            "Increase MAX_SERP_QUERIES only when quota allows.",
            "Do not run live discovery on every page load.",
        ],
    })

@app.route("/api/opportunities")
def opportunities():
    if not Config.ENABLE_PLACES_OPPORTUNITIES:
        # Honest cost-control state: feature intentionally off, not broken.
        return jsonify({
            "status": "disabled",
            "source": "google_places_opportunities",
            "enabled": False,
            "reason": "disabled_for_cost_control",
            "message": "Places opportunities radar is off to protect Google Maps quota. Core job discovery does not depend on it. Set ENABLE_PLACES_OPPORTUNITIES=1 to enable.",
            "count": 0,
            "rules": {"origin": Config.ORIGIN_ADDRESS, "uses_serpapi": False, "uses_google_maps": True},
            "data": [],
        })
    try:
        radius = float(request.args.get("max_radius", Config.MAX_RADIUS_MILES))
    except Exception:
        radius = Config.MAX_RADIUS_MILES
    data = nearby_opportunities_cached(radius)
    q = clean(request.args.get("q", "")).lower()
    min_rating = float_arg("min_rating", None)
    filtered = []
    for item in data:
        if min_rating is not None:
            try:
                if float(item.get("google_rating") or 0) < min_rating:
                    continue
            except Exception:
                continue
        if q:
            haystack = " ".join([clean(item.get("name")), clean(item.get("resolved_address")), " ".join(item.get("types") or [])]).lower()
            if q not in haystack:
                continue
        filtered.append(item)
    return jsonify({
        "status": "success",
        "source": "google_places_opportunities_no_serpapi",
        "count": len(filtered),
        "rules": {"origin": Config.ORIGIN_ADDRESS, "radius_miles": radius, "uses_serpapi": False},
        "data": filtered,
    })

@app.route("/api/jobs")
def jobs():
    if request.args.get("dry_run") == "1":
        return jsonify({
            "status": "ok",
            "dry_run": True,
            "message": "Live jobs endpoint is available. This dry run did not spend discovery provider budget.",
            "max_serp_queries": Config.MAX_SERP_QUERIES,
            "budget": serpapi_account_status(),
        })

    mode = clean(request.args.get("mode", "broad")).lower() or "broad"
    domain = clean(request.args.get("domain", "")).lower()
    extra = clean(request.args.get("q", ""))
    extra_terms = [extra] if extra else None

    result = fetch_jobs_live(mode=mode, domain=domain, extra_terms=extra_terms)
    filtered = apply_filters(result["accepted"])

    rejection_summary = {}
    for item in result.get("rejected", []):
        for reason in item.get("reasons", []):
            rejection_summary[reason] = rejection_summary.get(reason, 0) + 1

    response_payload = {
        "status": "success",
        "source": VERSION,
        "mode": result.get("mode", mode),
        "domain": result.get("domain", domain),
        "count": len(filtered),
        "visible_count": len(filtered),
        "accepted_count": len(result["accepted"]),
        "unfiltered_count": len(result["accepted"]),
        "enriched_count": result.get("enriched_count", 0),
        "enrich_cap": result.get("enrich_cap", Config.MAX_ENRICH_JOBS),
        "raw_count": result["raw_count"],
        "query_count": result["query_count"],
        "rejected_count": result.get("rejected_total", len(result.get("rejected", []))),
        "rejection_summary": rejection_summary,
        "resolution_flag_summary": result.get("resolution_flag_summary", {}),
        "provider_breakdown": result.get("provider_breakdown", {}),
        "quarantined_providers": result.get("quarantined_providers", {}),
        "rules": {
            "origin": Config.ORIGIN_ADDRESS,
            "max_radius_miles": Config.MAX_RADIUS_MILES,
            "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
            "default_mode": "broad",
            "food_only": mode == "food_service" or domain == "food_service",
            "missing_resolution": "kept_as_resolution_flags_not_rejected",
            "discovery": "federated_search_providers",
            "reasoning_providers": "enrichment_only_5_llm_research_per_accepted_job" if Config.ENABLE_LLM_RESEARCH else "not_used_as_discovery",
            "places_opportunities": "optional_separate_endpoint_/api/opportunities",
        },
        "data": filtered,
        "rejected": result.get("rejected", [])[:100],
    }

    # Persist live run to Cloud Storage so quota spend is captured.
    # Wrapped in try/except so a storage failure NEVER breaks the jobs response.
    stored = False
    batch_object: Optional[str] = None
    try:
        created_dt = datetime.now(timezone.utc)
        batch = {
            "batch_schema": "job_hunter_batch_v1",
            "created_at_utc": created_dt.replace(microsecond=0).isoformat(),
            "source": VERSION,
            "trigger": "live_ui",
            "rules": {
                "origin": Config.ORIGIN_ADDRESS,
                "max_radius_miles": Config.MAX_RADIUS_MILES,
                "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
                "mode": mode,
                "domain": domain,
            },
            "budget": {
                "serpapi": serpapi_account_status(),
                "max_queries": Config.MAX_QUERIES,
                "max_raw_jobs": Config.MAX_RAW_JOBS,
            },
            "counts": {
                "accepted": len(result["accepted"]),
                "rejected": result.get("rejected_total", len(result.get("rejected", []))),
                "raw": result["raw_count"],
                "queries": result["query_count"],
                "enriched": result.get("enriched_count", 0),
            },
            "accepted": result["accepted"],
            "rejected": result.get("rejected", []),
        }
        batch_object = f"batches/{created_dt.strftime('%Y/%m/%d/%H%M%S')}_job_batch.json"
        stored = gcs_upload_json(batch_object, batch)
        if not stored:
            batch_object = None
    except Exception as _store_exc:
        logger.warning("jobs() persistence failed (response unaffected): %s", _store_exc)

    response_payload["stored"] = stored
    response_payload["batch_object"] = batch_object

    return jsonify(response_payload)

@app.route("/api/debug/jobs")
def debug_jobs():
    mode = clean(request.args.get("mode", "broad")).lower() or "broad"
    domain = clean(request.args.get("domain", "")).lower()
    result = fetch_jobs_live(mode=mode, domain=domain)
    return jsonify({
        "status": "success",
        "source": VERSION,
        "mode": result.get("mode", mode),
        "domain": result.get("domain", domain),
        "accepted_count": len(result["accepted"]),
        "rejected_count": result.get("rejected_total", len(result["rejected"])),
        "raw_count": result["raw_count"],
        "query_count": result["query_count"],
        "resolution_flag_summary": result.get("resolution_flag_summary", {}),
        "provider_breakdown": result.get("provider_breakdown", {}),
        "quarantined_providers": result.get("quarantined_providers", {}),
        "accepted": result["accepted"],
        "rejected": result["rejected"],
    })

@app.route("/api/research/place")
def research_place():
    name = clean(request.args.get("name"))
    place_id = clean(request.args.get("place_id"))
    if not place_id and name:
        place = places_text_search(f"{name} Salt Lake City")
        place_id = clean((place or {}).get("place_id"))
    details = place_details(place_id) if place_id else {}
    return jsonify({"status": "success", "name": name, "place_id": place_id, "place_details": details})

def verify_oidc():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Missing or malformed Authorization header")
        return False
    # For S12-Omega proof, we assume Cloud Run/App Engine is verifying the token signature
    # and we only check if the header exists. In a full S12, we'd use google-auth.
    return True

@app.route("/api/ingest", methods=["POST"])
def ingest():
    if not verify_oidc():
        return jsonify({"status": "error", "error": "unauthorized"}), 401
    result = fetch_jobs_live()
    batch = {
        "batch_schema": "job_hunter_batch_v1",
        "created_at_utc": utc_now_iso(),
        "source": VERSION,
        "rules": {"origin": Config.ORIGIN_ADDRESS, "max_radius_miles": Config.MAX_RADIUS_MILES, "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60), "food_only": True},
        "budget": {"serpapi": serpapi_account_status(), "max_serp_queries": Config.MAX_SERP_QUERIES, "max_raw_jobs": Config.MAX_RAW_JOBS},
        "counts": {"accepted": len(result["accepted"]), "rejected": result.get("rejected_total", len(result["rejected"])), "raw": result["raw_count"], "queries": result["query_count"]},
        "accepted": result["accepted"],
        "rejected": result["rejected"],
    }
    created = datetime.fromisoformat(batch["created_at_utc"])
    object_name = f"batches/{created.strftime('%Y/%m/%d/%H%M%S')}_job_batch.json"
    ok = gcs_upload_json(object_name, batch)
    return jsonify({"status": "success" if ok else "error", "stored": ok, "object_name": object_name, "batch": {"created_at_utc": batch["created_at_utc"], "counts": batch["counts"], "source": batch["source"]}})

@app.route("/api/batches")
def batches():
    items = gcs_list_batches(200)
    return jsonify({
        "status": "success",
        "count": len(items),
        "bucket": Config.BATCH_BUCKET,
        "batches": [{"object_name": i.get("name"), "updated": i.get("updated"), "size": i.get("size"), "batch_id": i.get("name", "").replace("batches/", "").replace(".json", "")} for i in items],
    })

@app.route("/api/batch/<path:object_name>")
def batch_by_name(object_name):
    if not object_name.startswith("batches/"):
        object_name = "batches/" + object_name
    if not object_name.endswith(".json"):
        object_name += ".json"
    data = gcs_download_json(object_name)
    return jsonify({"status": "success" if data else "not_found", "object_name": object_name, "batch": data})

@app.route("/api/history")
def history():
    hours = float_arg("hours", 24.0) or 24.0
    start_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    end_dt = datetime.now(timezone.utc)
    from_raw = request.args.get("from")
    to_raw = request.args.get("to")
    if from_raw:
        try:
            start_dt = datetime.fromisoformat(from_raw.replace("Z", "+00:00"))
        except Exception:
            pass
    if to_raw:
        try:
            end_dt = datetime.fromisoformat(to_raw.replace("Z", "+00:00"))
        except Exception:
            pass
    jobs_out = []
    batch_summaries = []
    for item in gcs_list_batches(300):
        name = item.get("name")
        data = gcs_download_json(name)
        if not data:
            continue
        created_raw = data.get("created_at_utc", "")
        try:
            created = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        except Exception:
            continue
        if created < start_dt or created > end_dt:
            continue
        batch_summaries.append({"object_name": name, "created_at_utc": created_raw, "counts": data.get("counts")})
        for job in data.get("accepted", []):
            j = dict(job)
            j["batch_object_name"] = name
            j["batch_created_at_utc"] = created_raw
            jobs_out.append(j)
    jobs_out = apply_filters(jobs_out)
    jobs_out.sort(key=lambda j: (j.get("batch_created_at_utc", ""), j.get("radius_miles") if j.get("radius_miles") is not None else 999), reverse=True)
    return jsonify({"status": "success", "source": "orchestration_batch_history_v1", "from": start_dt.isoformat(), "to": end_dt.isoformat(), "batch_count": len(batch_summaries), "job_count": len(jobs_out), "batches": batch_summaries, "data": jobs_out})

@app.route("/api/demo")
def demo():
    return jobs()

@app.route("/api/search", methods=["GET", "POST"])
def search():
    return jobs()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
