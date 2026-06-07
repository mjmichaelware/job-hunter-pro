import os
import re
import json
import math
import logging
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import requests
from flask import Flask, jsonify, request, render_template_string

BASE_DIR = Path(__file__).resolve().parent.parent

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("job-hunter-pro")

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

session = requests.Session()

class Config:
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    XAI_API_KEY = os.environ.get("XAI_API_KEY", "").strip()

    ORIGIN_ADDRESS = os.environ.get(
        "ORIGIN_ADDRESS",
        "28 E Bryan Ave, Salt Lake City, UT 84115",
    ).strip()

    JOB_LOCATION = os.environ.get("JOB_LOCATION", "84115").strip()
    MAX_TRANSIT_SECONDS = int(os.environ.get("MAX_TRANSIT_SECONDS", "2100"))
    MAX_RADIUS_MILES = float(os.environ.get("MAX_RADIUS_MILES", "2.5"))
    REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "12"))
    MAX_SERP_QUERIES = int(os.environ.get("MAX_SERP_QUERIES", "16"))
    MAX_RAW_JOBS = int(os.environ.get("MAX_RAW_JOBS", "100"))
    MAX_AI_CALLS = int(os.environ.get("MAX_AI_CALLS", "24"))

VERSION = "ai_places_resolver_v3_definitive_food_fix"

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

FOOD_TERMS = [
    "restaurant", "waiter", "waitress", "server", "busser", "bussers",
    "food runner", "host", "hostess", "cook", "line cook", "prep cook",
    "dishwasher", "dishwashing", "kitchen", "chef", "sous chef",
    "barista", "cafe", "coffee", "bakery", "deli", "grill", "pizza",
    "sandwich", "dining", "food service", "culinary", "catering",
    "expo", "shift lead", "shift leader", "kitchen supervisor",
    "biscuit", "drink maker", "dish machine operator",
]

BAD_TERMS = [
    "software engineer", "developer", "registered nurse", "warehouse",
    "cdl", "forklift", "security guard", "mechanic", "medical assistant",
    "dental assistant", "teacher", "account executive", "sales representative",
]

def clean(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text if text else fallback

def clean_company(value: Any) -> str:
    text = clean(value)
    text = text.replace("-", " ")
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip(" -–—")
    return text

def term_present(text: str, term: str) -> bool:
    t = clean(text).lower()
    parts = [re.escape(part) for part in clean(term).lower().split()]
    if not parts:
        return False
    pattern = r"(?<![a-z0-9])" + r"\s+".join(parts) + r"(?![a-z0-9])"
    return re.search(pattern, t) is not None

def is_food_text(text: str) -> bool:
    t = clean(text).lower()

    food_hit = any(term_present(t, term) for term in FOOD_TERMS)
    if not food_hit:
        return False

    for bad in BAD_TERMS:
        if term_present(t, bad):
            return False

    return True

def parse_jsonish(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text or "", re.S)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {}

def chef_names_from_text(text: str) -> List[str]:
    names = []
    patterns = [
        r"\bexecutive chef\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        r"\bsous chef\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        r"\bchef\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text or ""):
            name = clean(match.group(1))
            if name and name not in names:
                names.append(name)

    return names[:5]

def miles_between(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    radius_miles = 3958.7613

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)

    h = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    )

    return 2 * radius_miles * math.asin(math.sqrt(h))

@lru_cache(maxsize=512)
def geocode(address: str) -> Optional[Tuple[float, float]]:
    address = clean(address)
    if not address or not Config.GOOGLE_MAPS_API_KEY:
        return None

    try:
        res = session.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "address": address,
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()

        if data.get("status") != "OK" or not data.get("results"):
            return None

        loc = data["results"][0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])

    except Exception as exc:
        logger.warning("geocode failed for %s: %s", address, exc)
        return None

def origin_latlng() -> Optional[Tuple[float, float]]:
    return geocode(Config.ORIGIN_ADDRESS)

@lru_cache(maxsize=1)
def nearby_restaurants() -> List[Dict[str, Any]]:
    origin = origin_latlng()
    if not origin or not Config.GOOGLE_MAPS_API_KEY:
        return []

    try:
        res = session.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "location": f"{origin[0]},{origin[1]}",
                "radius": int(Config.MAX_RADIUS_MILES * 1609.344),
                "type": "restaurant",
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()

        out = []
        for item in data.get("results", []) or []:
            loc = item.get("geometry", {}).get("location", {})
            latlng = None

            if "lat" in loc and "lng" in loc:
                latlng = (float(loc["lat"]), float(loc["lng"]))

            out.append({
                "name": clean(item.get("name")),
                "place_id": clean(item.get("place_id")),
                "vicinity": clean(item.get("vicinity")),
                "rating": item.get("rating"),
                "latlng": latlng,
                "types": item.get("types", []),
            })

        return out

    except Exception as exc:
        logger.warning("nearby restaurants failed: %s", exc)
        return []

@lru_cache(maxsize=1024)
def places_text_search(query: str) -> Optional[Dict[str, Any]]:
    query = clean(query)
    origin = origin_latlng()

    if not query or not origin or not Config.GOOGLE_MAPS_API_KEY:
        return None

    try:
        res = session.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={
                "query": query,
                "location": f"{origin[0]},{origin[1]}",
                "radius": int(max(Config.MAX_RADIUS_MILES, 3.0) * 1609.344),
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
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
        logger.warning("places search failed for %s: %s", query, exc)
        return None

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
        res = session.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params={
                "origins": Config.ORIGIN_ADDRESS,
                "destinations": destination,
                "mode": "transit",
                "departure_time": "now",
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
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
        logger.warning("transit lookup failed for %s: %s", destination, exc)
        return empty

def explicit_address_from_raw(raw: Dict[str, Any]) -> str:
    text = " ".join([
        clean(raw.get("title")),
        clean_company(raw.get("company_name") or raw.get("company")),
        clean(raw.get("location")),
        clean(raw.get("description")),
    ])

    patterns = [
        r"\b\d{1,6}\s+[NESW]?\s*[A-Za-z0-9.' -]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Way|Ct|Court|Ln|Lane|Expy|Expressway|Pkwy|Parkway|Hwy|Highway)\s+Salt Lake City,?\s*UT\s*\d{5}\b",
        r"\b\d{1,6}\s+[NESW]?\s*[A-Za-z0-9.' -]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Way|Ct|Court|Ln|Lane|Expy|Expressway|Pkwy|Parkway|Hwy|Highway)\b",
        r"\b\d{1,6}\s+[NESW]\s+\d{1,6}\s+[NESW]\b",
        r"\b\d{1,6}\s+\d{1,6}\s+[NESW]\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            addr = clean(match.group(0))
            if "salt lake" not in addr.lower():
                addr = f"{addr}, Salt Lake City, UT"
            return addr

    return ""

def generic_place_query(query: str) -> bool:
    q = clean(query).lower()

    generic_exact = {
        "salt lake city hotel",
        "salt lake city restaurant",
        "restaurant near 84115 salt lake city ut",
        "hotel near 84115 salt lake city ut",
        "food service near 84115 salt lake city ut",
        "jobs near 84115 salt lake city ut",
    }

    if q in generic_exact:
        return True

    generic_patterns = [
        r"^salt lake city\s+(hotel|restaurant|bar|cafe)$",
        r"^(hotel|restaurant|bar|cafe)\s+near\s+84115",
        r"^restaurants?\s+in\s+salt lake city",
    ]

    return any(re.search(pattern, q) for pattern in generic_patterns)

def serpapi_jobs(query: str) -> List[Dict[str, Any]]:
    if not Config.SERPAPI_KEY:
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
        logger.warning("serpapi failed for %s: %s", query, exc)
        return []

def ai_prompt(raw: Dict[str, Any]) -> str:
    return f"""Return ONLY compact JSON.

Extract restaurant job intelligence from this listing.

Keys:
restaurant_name: string or null
role: string or null
chef_names: array of strings
is_food_service: boolean
google_place_queries: array of 1-5 specific Google Maps search queries

Rules:
- Prefer the actual restaurant/cafe/bar/hotel restaurant name.
- Do not return generic queries like "Salt Lake City hotel".
- Do not invent street addresses.
- If company is a restaurant chain, use that company name.
- Use 84115 Salt Lake City context.

Title: {clean(raw.get("title"))}
Company: {clean_company(raw.get("company_name") or raw.get("company"))}
Location: {clean(raw.get("location"))}
Description: {clean(raw.get("description"))[:1600]}
"""

def openai_like_extract(provider: str, key: str, base_url: str, model: str, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not key:
        return None

    try:
        res = session.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "temperature": 0,
                "messages": [
                    {
                        "role": "system",
                        "content": "You extract factual restaurant job entities. Return JSON only.",
                    },
                    {
                        "role": "user",
                        "content": ai_prompt(raw),
                    },
                ],
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        text = res.json()["choices"][0]["message"]["content"]
        data = parse_jsonish(text)

        if data:
            data["_provider"] = provider
            return data

    except Exception as exc:
        logger.warning("%s AI extraction failed: %s", provider, exc)

    return None

def gemini_extract(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not Config.GEMINI_API_KEY:
        return None

    try:
        res = session.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
            params={"key": Config.GEMINI_API_KEY},
            json={
                "contents": [{"parts": [{"text": ai_prompt(raw)}]}],
                "generationConfig": {
                    "temperature": 0,
                    "responseMimeType": "application/json",
                },
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        data = parse_jsonish(text)

        if data:
            data["_provider"] = "gemini"
            return data

    except Exception as exc:
        logger.warning("gemini extraction failed: %s", exc)

    return None

def anthropic_extract(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not Config.ANTHROPIC_API_KEY:
        return None

    try:
        res = session.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": Config.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": "claude-3-5-haiku-latest",
                "max_tokens": 600,
                "temperature": 0,
                "messages": [{"role": "user", "content": ai_prompt(raw)}],
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        text = "".join(
            part.get("text", "")
            for part in res.json().get("content", [])
            if part.get("type") == "text"
        )
        data = parse_jsonish(text)

        if data:
            data["_provider"] = "claude"
            return data

    except Exception as exc:
        logger.warning("claude extraction failed: %s", exc)

    return None

AI_CALL_COUNT = 0

def deterministic_extract(raw: Dict[str, Any]) -> Dict[str, Any]:
    title = clean(raw.get("title"))
    company = clean_company(raw.get("company_name") or raw.get("company"))
    location = clean(raw.get("location"))
    description = clean(raw.get("description"))
    text = " ".join([title, company, location, description])

    queries = []

    for query in [
        f"{company} Salt Lake City",
        f"{company} restaurant Salt Lake City",
        f"{company} near 84115 Salt Lake City UT",
        f"{company} {title} Salt Lake City",
    ]:
        query = clean(query)
        if company and query not in queries and not generic_place_query(query):
            queries.append(query)

    return {
        "restaurant_name": company or None,
        "role": title or None,
        "chef_names": chef_names_from_text(text),
        "is_food_service": is_food_text(text),
        "google_place_queries": queries[:5],
        "_provider": "deterministic",
    }

def ai_extract(raw: Dict[str, Any]) -> Dict[str, Any]:
    global AI_CALL_COUNT

    base = deterministic_extract(raw)

    if not base.get("is_food_service"):
        return base

    if AI_CALL_COUNT >= Config.MAX_AI_CALLS:
        return base

    providers = [
        lambda: openai_like_extract("groq", Config.GROQ_API_KEY, "https://api.groq.com/openai/v1", "llama-3.1-8b-instant", raw),
        lambda: openai_like_extract("openai", Config.OPENAI_API_KEY, "https://api.openai.com/v1", os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), raw),
        lambda: gemini_extract(raw),
        lambda: anthropic_extract(raw),
        lambda: openai_like_extract("xai_grok", Config.XAI_API_KEY, "https://api.x.ai/v1", os.environ.get("XAI_MODEL", "grok-2-latest"), raw),
    ]

    for provider in providers:
        AI_CALL_COUNT += 1
        data = provider()

        if not data:
            continue

        queries = [
            clean(q)
            for q in data.get("google_place_queries", []) or []
            if clean(q) and not generic_place_query(clean(q))
        ]

        if queries:
            data["google_place_queries"] = queries
            return data

    return base

def resolve_place(raw: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
    company = clean_company(raw.get("company_name") or raw.get("company"))
    title = clean(raw.get("title"))
    ai_name = clean_company(ai.get("restaurant_name"))

    explicit = explicit_address_from_raw(raw)
    if explicit:
        latlng = geocode(explicit)
        return {
            "name": ai_name or company,
            "formatted_address": explicit,
            "place_id": "",
            "rating": None,
            "types": ["explicit_address_from_listing"],
            "latlng": latlng,
            "query_used": "explicit_address_from_listing",
        }

    queries = []

    for name in [ai_name, company]:
        name = clean_company(name)
        if not name:
            continue

        for query in [
            f"{name} Salt Lake City",
            f"{name} restaurant Salt Lake City",
            f"{name} near 84115 Salt Lake City UT",
        ]:
            query = clean(query)
            if query and not generic_place_query(query) and query not in queries:
                queries.append(query)

    for query in ai.get("google_place_queries", []) or []:
        query = clean(query)
        if query and not generic_place_query(query) and query not in queries:
            queries.append(query)

    for query in [
        f"{company} {title} Salt Lake City",
        f"{company} {title} near 84115 Salt Lake City UT",
    ]:
        query = clean(query)
        if company and query and not generic_place_query(query) and query not in queries:
            queries.append(query)

    for query in queries[:10]:
        place = places_text_search(query)
        if place and place.get("formatted_address") and place.get("latlng"):
            return place

    return {
        "name": "",
        "formatted_address": "",
        "place_id": "",
        "rating": None,
        "types": [],
        "latlng": None,
        "query_used": "",
    }

def salary(raw: Dict[str, Any]) -> str:
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

    description = clean(raw.get("description"))
    match = re.search(r"\$\s?\d+(?:\.\d+)?\s*(?:-|to)?\s*\$?\s?\d*(?:\.\d+)?\s*(?:/ ?hr|/ ?hour|per hour|an hour)?", description, re.I)

    if match:
        return clean(match.group(0))

    return "Salary not listed"

def apply_link(raw: Dict[str, Any]) -> str:
    options = raw.get("apply_options")

    if isinstance(options, list) and options:
        first = options[0]
        if isinstance(first, dict):
            return clean(first.get("link"))

    return ""

def tags_for(job: Dict[str, Any]) -> List[str]:
    text = " ".join([
        clean(job.get("title")),
        clean(job.get("description")),
        clean(job.get("company")),
        clean(job.get("restaurant_name")),
    ]).lower()

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

    return tags[:5] or ["food-service"]

def match_score(job: Dict[str, Any]) -> int:
    score = 70
    text = " ".join([
        clean(job.get("title")),
        clean(job.get("description")),
        clean(job.get("restaurant_name")),
    ]).lower()

    boosts = {
        "line cook": 10,
        "prep cook": 10,
        "cook": 8,
        "server": 7,
        "waiter": 7,
        "waitress": 7,
        "busser": 7,
        "food runner": 7,
        "host": 6,
        "hostess": 6,
        "dishwasher": 6,
        "chef": 6,
        "restaurant": 7,
        "kitchen": 8,
    }

    for word, points in boosts.items():
        if term_present(text, word):
            score += points

    commute = job.get("commute_seconds")
    radius = job.get("radius_miles")

    if commute is not None:
        if commute <= 900:
            score += 10
        elif commute <= 1500:
            score += 7
        elif commute < Config.MAX_TRANSIT_SECONDS:
            score += 3
        else:
            score -= 10

    if radius is not None:
        if radius <= 1:
            score += 10
        elif radius <= 2:
            score += 6
        elif radius <= Config.MAX_RADIUS_MILES:
            score += 3
        else:
            score -= 10

    if job.get("resolved_address"):
        score += 5

    return max(1, min(score, 99))

def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    ai = ai_extract(raw)
    place = resolve_place(raw, ai)

    title = clean(raw.get("title"), "Untitled Restaurant Role")
    company = clean_company(raw.get("company_name") or raw.get("company")) or "Company not listed"
    listing_location = clean(raw.get("location"), Config.JOB_LOCATION)
    description = clean(raw.get("description"), "No description available.")

    resolved_address = clean(place.get("formatted_address"))
    resolved_name = clean(place.get("name"))
    destination = resolved_address or listing_location

    transit = transit_to(destination)
    origin = origin_latlng()

    radius_miles = None
    radius_label = "Radius unavailable"

    if origin and place.get("latlng"):
        radius_miles = round(miles_between(origin, place["latlng"]), 2)
        radius_label = f"{radius_miles} mi radius"

    job = {
        "title": title,
        "company": company,
        "restaurant_name": clean_company(ai.get("restaurant_name")) or resolved_name or company,
        "resolved_place_name": resolved_name,
        "resolved_address": resolved_address,
        "location": resolved_address or listing_location,
        "listing_location": listing_location,
        "salary": salary(raw),
        "description": description,
        "commute_seconds": transit["commute_seconds"],
        "commute_label": transit["commute_label"],
        "radius_miles": radius_miles,
        "radius_label": radius_label,
        "distance_miles": radius_miles,
        "distance_label": radius_label,
        "transit_distance_miles": transit["transit_distance_miles"],
        "transit_distance_label": transit["transit_distance_label"],
        "source_url": apply_link(raw),
        "job_id": clean(raw.get("job_id")),
        "via": clean(raw.get("via")),
        "ai_provider": ai.get("_provider"),
        "chef_names": ai.get("chef_names") or chef_names_from_text(description),
        "place_query_used": place.get("query_used"),
        "place_id": place.get("place_id"),
        "place_rating": place.get("rating"),
    }

    job["tags"] = tags_for(job)
    job["match"] = match_score(job)

    return job

def rejection_reasons(job: Dict[str, Any]) -> List[str]:
    reasons = []

    food_text = " ".join([
        clean(job.get("title")),
        clean(job.get("company")),
        clean(job.get("description")),
        clean(job.get("restaurant_name")),
        clean(job.get("resolved_place_name")),
        " ".join(job.get("tags") or []),
    ])

    if not is_food_text(food_text):
        reasons.append("not_food_service")

    if not job.get("resolved_address"):
        reasons.append("no_exact_restaurant_address_resolved")

    if job.get("radius_miles") is None:
        reasons.append("radius_unavailable")
    elif job["radius_miles"] > Config.MAX_RADIUS_MILES:
        reasons.append(f"outside_radius_{job['radius_miles']}mi")

    if job.get("commute_seconds") is None:
        reasons.append("transit_unavailable")
    elif job["commute_seconds"] >= Config.MAX_TRANSIT_SECONDS:
        reasons.append(f"transit_too_long_{round(job['commute_seconds'] / 60)}min")

    return reasons

def raw_job_queries() -> List[str]:
    queries = list(ROLE_QUERIES)

    for restaurant in nearby_restaurants()[:12]:
        name = clean(restaurant.get("name"))
        if name:
            queries.append(f'"{name}" restaurant jobs Salt Lake City')
            queries.append(f'"{name}" server cook dishwasher jobs')

    unique = []

    for query in queries:
        if query not in unique:
            unique.append(query)

    return unique[:Config.MAX_SERP_QUERIES]

def fetch_jobs() -> Dict[str, Any]:
    global AI_CALL_COUNT
    AI_CALL_COUNT = 0

    seen = set()
    raw_jobs = []

    for query in raw_job_queries():
        for raw in serpapi_jobs(query):
            identity = (
                clean(raw.get("job_id"))
                or clean(raw.get("title")) + clean(raw.get("company_name")) + clean(raw.get("location"))
            )

            if identity and identity not in seen:
                seen.add(identity)
                raw["_query_used"] = query
                raw_jobs.append(raw)

            if len(raw_jobs) >= Config.MAX_RAW_JOBS:
                break

        if len(raw_jobs) >= Config.MAX_RAW_JOBS:
            break

    accepted = []
    rejected = []

    for raw in raw_jobs:
        job = normalize(raw)
        reasons = rejection_reasons(job)

        if reasons:
            rejected.append({
                "query": raw.get("_query_used"),
                "title": job.get("title"),
                "company": job.get("company"),
                "restaurant_name": job.get("restaurant_name"),
                "resolved_place_name": job.get("resolved_place_name"),
                "listing_location": job.get("listing_location"),
                "resolved_address": job.get("resolved_address"),
                "commute_label": job.get("commute_label"),
                "radius_label": job.get("radius_label"),
                "ai_provider": job.get("ai_provider"),
                "place_query_used": job.get("place_query_used"),
                "tags": job.get("tags"),
                "source_url": job.get("source_url"),
                "reasons": reasons,
            })
        else:
            accepted.append(job)

    accepted.sort(key=lambda job: (
        job.get("radius_miles") if job.get("radius_miles") is not None else 999,
        job.get("commute_seconds") if job.get("commute_seconds") is not None else 999999,
        -job.get("match", 0),
    ))

    return {
        "raw_count": len(raw_jobs),
        "query_count": len(raw_job_queries()),
        "nearby_restaurant_count": len(nearby_restaurants()),
        "accepted": accepted[:30],
        "rejected": rejected[:100],
    }

@app.after_request
def headers(response):
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
  <main class="container section">
    <p class="kicker">Cloud Run Online</p>
    <h1 class="text-gradient">Job Hunter Pro</h1>
    <p class="lead">Live restaurant jobs resolved through AI + Google Places, filtered by 2.5 mile radius and under 35 minute transit.</p>
    <div class="cluster">
      <a class="btn btn-primary" href="/api/health">Health</a>
      <button class="btn btn-ghost" onclick="loadJobs()">Refresh Restaurant Jobs</button>
      <a class="btn btn-ghost" href="/api/debug/jobs">Debug</a>
    </div>
    <p class="status-line" id="status">Loading live jobs...</p>
    <section class="grid-system" id="jobs"></section>
  </main>
  <div class="noise"></div>
  <script src="/static/js/main.js"></script>
  <script>
    function loadJobs(){
      const s = document.getElementById('status');
      s.textContent = 'Searching live jobs with AI + Google Places...';
      fetch('/api/jobs')
        .then(r => r.json())
        .then(p => {
          s.textContent = `Showing ${p.count || 0} strict-matched jobs. Raw scanned: ${p.raw_count || 0}. Nearby restaurants: ${p.nearby_restaurant_count || 0}.`;
          window.UI && window.UI.renderJobs(p.data || []);
        })
        .catch(e => {
          console.error(e);
          s.textContent = 'Search failed. Open Debug.';
        });
    }
    loadJobs();
  </script>
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
        "nearby_restaurant_count": len(nearby_restaurants()),
        "pipeline": [
            "Google Places nearby restaurants",
            "SerpAPI Google Jobs",
            "exact food phrase matching",
            "AI restaurant entity extraction",
            "explicit address extraction",
            "safe Google Places Text Search",
            "Google Distance Matrix transit",
            "strict radius/transit filter",
        ],
    })

@app.route("/api/ai/status")
def ai_status():
    return health()

@app.route("/api/jobs")
def jobs():
    result = fetch_jobs()
    return jsonify({
        "status": "success",
        "source": VERSION,
        "count": len(result["accepted"]),
        "raw_count": result["raw_count"],
        "query_count": result["query_count"],
        "nearby_restaurant_count": result["nearby_restaurant_count"],
        "rules": {
            "origin": Config.ORIGIN_ADDRESS,
            "max_radius_miles": Config.MAX_RADIUS_MILES,
            "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
            "food_only": True,
        },
        "data": result["accepted"],
    })

@app.route("/api/debug/jobs")
def debug_jobs():
    result = fetch_jobs()
    return jsonify({
        "status": "success",
        "source": VERSION,
        "accepted_count": len(result["accepted"]),
        "rejected_count": len(result["rejected"]),
        "raw_count": result["raw_count"],
        "query_count": result["query_count"],
        "nearby_restaurant_count": result["nearby_restaurant_count"],
        "rules": {
            "origin": Config.ORIGIN_ADDRESS,
            "max_radius_miles": Config.MAX_RADIUS_MILES,
            "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
            "food_only": True,
        },
        "accepted": result["accepted"],
        "rejected": result["rejected"],
    })

@app.route("/api/demo")
def demo():
    return jobs()

@app.route("/api/search", methods=["GET", "POST"])
def search():
    return jobs()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
