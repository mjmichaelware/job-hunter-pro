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

VERSION = "ai_places_resolver_v7_orchestrated_dashboard"

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
    account = serpapi_account_status()
    left = account.get("total_searches_left")
    if left is None:
        return True
    try:
        return int(left) > Config.SERPAPI_MIN_SEARCHES_LEFT
    except Exception:
        return True

def serpapi_jobs(query: str) -> List[Dict[str, Any]]:
    if not Config.SERPAPI_KEY:
        return []

    if not serpapi_budget_allows_search():
        logger.warning("SerpAPI budget guard stopped search: %s", query)
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



POSITIVE_REVIEW_TERMS = [
    "great", "excellent", "amazing", "friendly", "clean", "fast", "organized",
    "professional", "supportive", "respectful", "good management", "good tips",
    "flexible", "team", "positive", "stable", "fair", "busy", "popular"
]

NEGATIVE_REVIEW_TERMS = [
    "toxic", "rude", "dirty", "slow", "unorganized", "chaotic", "bad management",
    "underpaid", "low pay", "harassment", "unsafe", "high turnover", "stressful",
    "short staffed", "micromanage", "favoritism", "hostile", "late pay"
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

def role_family_for_job(job: Dict[str, Any]) -> str:
    text = " ".join([
        clean(job.get("title")),
        clean(job.get("description")),
        clean(job.get("restaurant_name")),
        " ".join(job.get("tags") or []),
    ]).lower()

    for term, family in ROLE_GROUPS.items():
        if term_present(text, term):
            return family

    return "food-service"

@lru_cache(maxsize=1024)
def place_details(place_id: str) -> Dict[str, Any]:
    place_id = clean(place_id)
    if not place_id or not Config.GOOGLE_MAPS_API_KEY:
        return {}

    try:
        res = session.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "name,rating,user_ratings_total,reviews,price_level,website,url,business_status,formatted_phone_number,opening_hours",
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()

        if data.get("status") != "OK":
            return {}

        return data.get("result") or {}

    except Exception as exc:
        logger.warning("place details failed for %s: %s", place_id, exc)
        return {}

@lru_cache(maxsize=512)
def web_search(query: str, limit: int = 5) -> List[Dict[str, str]]:
    query = clean(query)
    if not query or not Config.SERPAPI_KEY:
        return []

    try:
        res = session.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google",
                "q": query,
                "location": "Salt Lake City, Utah, United States",
                "hl": "en",
                "gl": "us",
                "num": limit,
                "api_key": Config.SERPAPI_KEY,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()

        out = []
        for item in data.get("organic_results", [])[:limit]:
            out.append({
                "title": clean(item.get("title")),
                "link": clean(item.get("link")),
                "snippet": clean(item.get("snippet")),
                "source": clean(item.get("source")),
            })

        return out

    except Exception as exc:
        logger.warning("web search failed for %s: %s", query, exc)
        return []

def count_terms(text: str, terms: List[str]) -> int:
    text = clean(text).lower()
    total = 0

    for term in terms:
        if term in text:
            total += 1

    return total

def review_score(google_rating, review_count, combined_text: str) -> Dict[str, Any]:
    try:
        rating = float(google_rating or 0)
    except Exception:
        rating = 0.0

    try:
        count = int(review_count or 0)
    except Exception:
        count = 0

    positive = count_terms(combined_text, POSITIVE_REVIEW_TERMS)
    negative = count_terms(combined_text, NEGATIVE_REVIEW_TERMS)

    rating_component = (rating / 5.0) * 100 if rating else 50
    volume_component = min(20, math.log10(count + 1) * 10) if count else 0
    sentiment_component = max(-25, min(25, (positive - negative) * 4))

    score = round(max(0, min(100, rating_component + volume_component + sentiment_component)))

    consistency_penalty = min(45, negative * 7)
    consistency = round(max(0, min(100, 100 - consistency_penalty + min(10, positive * 2))))

    risk = "low"
    if score < 55 or consistency < 55:
        risk = "high"
    elif score < 70 or consistency < 70:
        risk = "medium"

    return {
        "review_score": score,
        "consistency_score": consistency,
        "positive_signal_count": positive,
        "negative_signal_count": negative,
        "risk_level": risk,
    }

def build_review_intelligence(job: Dict[str, Any]) -> Dict[str, Any]:
    restaurant = clean(job.get("restaurant_name") or job.get("resolved_place_name") or job.get("company"))
    address = clean(job.get("resolved_address") or job.get("location"))
    place_id = clean(job.get("place_id"))

    details = place_details(place_id)
    google_rating = details.get("rating", job.get("place_rating"))
    google_review_count = details.get("user_ratings_total")

    google_reviews = []
    for r in details.get("reviews", []) or []:
        google_reviews.append({
            "author": clean(r.get("author_name")),
            "rating": r.get("rating"),
            "relative_time": clean(r.get("relative_time_description")),
            "text": clean(r.get("text")),
        })

    review_queries = [
        f'"{restaurant}" reviews Salt Lake City',
        f'"{restaurant}" employee reviews restaurant',
        f'"{restaurant}" Glassdoor OR Indeed reviews',
    ]

    chef_queries = [
        f'"{restaurant}" chef Salt Lake City',
        f'"{restaurant}" executive chef',
        f'"{restaurant}" sous chef',
    ]

    public_review_results = []
    chef_public_results = []

    for q in review_queries:
        public_review_results.extend(web_search(q, 4))

    for q in chef_queries:
        chef_public_results.extend(web_search(q, 3))

    seen_links = set()
    deduped_reviews = []
    for item in public_review_results:
        link = item.get("link")
        if link and link not in seen_links:
            seen_links.add(link)
            deduped_reviews.append(item)

    seen_links = set()
    deduped_chef = []
    for item in chef_public_results:
        link = item.get("link")
        if link and link not in seen_links:
            seen_links.add(link)
            deduped_chef.append(item)

    combined_text = " ".join(
        [restaurant, address, clean(job.get("description"))]
        + [r.get("text", "") for r in google_reviews]
        + [r.get("snippet", "") for r in deduped_reviews]
        + [r.get("snippet", "") for r in deduped_chef]
    )

    score = review_score(google_rating, google_review_count, combined_text)

    chef_names = list(job.get("chef_names") or [])
    for item in deduped_chef:
        for name in chef_names_from_text(item.get("snippet", "")):
            if name not in chef_names:
                chef_names.append(name)

    return {
        "google_rating": google_rating,
        "google_review_count": google_review_count,
        "google_reviews_sample": google_reviews[:5],
        "public_review_results": deduped_reviews[:8],
        "chef_public_results": deduped_chef[:6],
        "chef_names": chef_names[:8],
        "website": clean(details.get("website")),
        "google_maps_url": clean(details.get("url")),
        "phone": clean(details.get("formatted_phone_number")),
        "business_status": clean(details.get("business_status")),
        **score,
    }

def enrich_job_for_filters(job: Dict[str, Any]) -> Dict[str, Any]:
    j = dict(job)
    j["role_family"] = role_family_for_job(j)
    j["review_intelligence"] = build_review_intelligence(j)

    ri = j["review_intelligence"]
    j["google_rating"] = ri.get("google_rating")
    j["google_review_count"] = ri.get("google_review_count")
    j["review_score"] = ri.get("review_score")
    j["consistency_score"] = ri.get("consistency_score")
    j["risk_level"] = ri.get("risk_level")
    j["chef_names"] = ri.get("chef_names") or j.get("chef_names") or []

    return j

def float_arg(name: str, default: Optional[float]) -> Optional[float]:
    value = request.args.get(name)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except Exception:
        return default

def str_arg(name: str, default: str = "") -> str:
    return clean(request.args.get(name), default)

def apply_user_filters(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    min_rating = float_arg("min_rating", None)
    max_radius = float_arg("max_radius", None)
    max_transit = float_arg("max_transit", None)
    min_score = float_arg("min_score", None)

    role = str_arg("role", "all").lower()
    house = str_arg("house", "all").lower()
    q = str_arg("q", "").lower()

    out = []

    for job in jobs:
        if min_rating is not None:
            try:
                if float(job.get("google_rating") or 0) < min_rating:
                    continue
            except Exception:
                continue

        if max_radius is not None:
            try:
                if float(job.get("radius_miles")) > max_radius:
                    continue
            except Exception:
                continue

        if max_transit is not None:
            try:
                if float(job.get("commute_seconds")) / 60 > max_transit:
                    continue
            except Exception:
                continue

        if min_score is not None:
            try:
                if float(job.get("review_score") or 0) < min_score:
                    continue
            except Exception:
                continue

        tags = [clean(t).lower() for t in job.get("tags") or []]
        title = clean(job.get("title")).lower()
        role_text = " ".join(tags + [title])

        if role and role != "all":
            if role not in role_text:
                continue

        if house and house != "all":
            if clean(job.get("role_family")).lower() != house:
                continue

        if q:
            haystack = " ".join([
                clean(job.get("title")),
                clean(job.get("restaurant_name")),
                clean(job.get("resolved_address")),
                clean(job.get("description")),
                " ".join(tags),
            ]).lower()

            if q not in haystack:
                continue

        out.append(job)

    return out


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
  <aside class="app-sidebar">
    <div class="brand">JHP</div>
    <a href="#overview">Overview</a>
    <a href="#filters">Filters</a>
    <a href="#jobs">Live Jobs</a>
    <a href="#opportunities">Opportunities</a>
    <a href="#history">History</a>
    <a href="/api/usage">Usage</a>
    <a href="/api/why-three">Why only a few?</a>
  </aside>

  <main class="app-shell">
    <section class="hero-panel" id="overview">
      <p class="kicker">Persistent AI Job Intelligence</p>
      <h1 class="text-gradient">Job Hunter Pro</h1>
      <p class="lead">A Google Cloud Run application that combines SerpAPI job discovery, Google Places restaurant intelligence, Maps transit/radius scoring, LLM entity extraction, public review signals, persistent batch history, and filterable UI/UX.</p>
      <div class="cluster">
        <button class="btn btn-primary" onclick="loadLiveJobs()">Run Live Job Discovery</button>
        <button class="btn btn-ghost" onclick="loadOpportunities()">Load Restaurant Opportunities</button>
        <button class="btn btn-ghost" onclick="loadHistory()">Load Last 24h History</button>
      </div>
    </section>

    <section class="stats-grid">
      <div class="stat-card"><strong id="statJobs">—</strong><span>visible jobs</span></div>
      <div class="stat-card"><strong id="statRaw">—</strong><span>raw jobs scanned</span></div>
      <div class="stat-card"><strong id="statOpps">—</strong><span>nearby opportunities</span></div>
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
      <h2>Live / Historical Jobs</h2>
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
      <p>This application is designed as a persistent, multi-intelligence job research system: it discovers listings, resolves real restaurant locations, checks commute and radius, enriches with reviews and public signals, stores timestamped batches, and lets you inspect jobs by filters and time ranges.</p>
    </section>
  </main>

  <script src="/static/js/main.js"></script>
  <script>
    function val(id){ return document.getElementById(id)?.value || ""; }

    function params(){
      const p = new URLSearchParams();
      for (const id of ["min_rating","max_radius","max_transit","min_score","role","house","q"]) {
        const v = val(id);
        if (v && v !== "all") p.set(id, v);
      }
      return p.toString();
    }

    function setStatus(t){ document.getElementById("status").textContent = t; }

    function updateStats(p){
      if ("count" in p) document.getElementById("statJobs").textContent = p.count;
      if ("raw_count" in p) document.getElementById("statRaw").textContent = p.raw_count;
      if ("nearby_restaurant_count" in p) document.getElementById("statOpps").textContent = p.nearby_restaurant_count;
    }

    function loadUsage(){
      fetch("/api/usage").then(r=>r.json()).then(p=>{
        const left = p?.serpapi?.total_searches_left ?? "—";
        document.getElementById("statSerp").textContent = left;
      }).catch(()=>{});
    }

    function loadLiveJobs(){
      const qs = params();
      setStatus("Running budget-limited live discovery...");
      fetch("/api/jobs" + (qs ? "?" + qs : ""))
        .then(r=>r.json())
        .then(p=>{
          updateStats(p);
          setStatus(`Live jobs loaded: ${p.count || 0}. Raw scanned: ${p.raw_count || 0}.`);
          window.UI && window.UI.renderJobsInto("jobGrid", p.data || []);
        })
        .catch(e=>setStatus("Live job load failed: " + e));
    }

    function loadOpportunities(){
      const qs = params();
      setStatus("Loading Google Places restaurant opportunities without SerpAPI...");
      fetch("/api/opportunities" + (qs ? "?" + qs : ""))
        .then(r=>r.json())
        .then(p=>{
          document.getElementById("statOpps").textContent = p.count || 0;
          setStatus(`Loaded ${p.count || 0} nearby restaurant opportunities.`);
          const rows = (p.data || []).map(x => `
            <tr>
              <td>${escapeHTML(x.name || "")}</td>
              <td>${escapeHTML(x.google_rating || "—")}</td>
              <td>${escapeHTML(x.google_review_count || "—")}</td>
              <td>${escapeHTML(x.radius_label || "—")}</td>
              <td>${escapeHTML(x.business_status || "—")}</td>
              <td>${x.place_id ? `<a href="/api/research/place?place_id=${escapeHTML(x.place_id)}&name=${encodeURIComponent(x.name || "")}" target="_blank">Research</a>` : ""}</td>
            </tr>`).join("");
          document.getElementById("opportunityRows").innerHTML = rows || "<tr><td colspan='6'>No opportunities loaded.</td></tr>";
        })
        .catch(e=>setStatus("Opportunities failed: " + e));
    }

    function loadHistory(){
      const qs = params();
      setStatus("Loading stored batch history...");
      fetch("/api/history?hours=24" + (qs ? "&" + qs : ""))
        .then(r=>r.json())
        .then(p=>{
          document.getElementById("statJobs").textContent = p.job_count || 0;
          setStatus(`History loaded: ${p.job_count || 0} jobs across ${p.batch_count || 0} batches.`);
          window.UI && window.UI.renderJobsInto("jobGrid", p.data || []);
          const rows = (p.batches || []).map(b => `
            <tr>
              <td>${escapeHTML(b.object_name || "")}</td>
              <td>${escapeHTML(b.created_at_utc || "")}</td>
              <td>${escapeHTML(b.counts?.accepted ?? "—")}</td>
              <td>${escapeHTML(b.counts?.rejected ?? "—")}</td>
              <td>${escapeHTML(b.counts?.raw ?? "—")}</td>
            </tr>`).join("");
          document.getElementById("historyRows").innerHTML = rows || "<tr><td colspan='5'>No batches stored yet.</td></tr>";
        })
        .catch(e=>setStatus("History failed: " + e));
    }

    loadUsage();
    loadOpportunities();
    loadHistory();
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

    enriched = [enrich_job_for_filters(job) for job in result["accepted"]]
    filtered = apply_user_filters(enriched)

    return jsonify({
        "status": "success",
        "source": VERSION,
        "count": len(filtered),
        "unfiltered_count": len(enriched),
        "raw_count": result["raw_count"],
        "query_count": result["query_count"],
        "nearby_restaurant_count": result["nearby_restaurant_count"],
        "filters": {
            "min_rating": request.args.get("min_rating"),
            "max_radius": request.args.get("max_radius"),
            "max_transit": request.args.get("max_transit"),
            "min_score": request.args.get("min_score"),
            "role": request.args.get("role"),
            "house": request.args.get("house"),
            "q": request.args.get("q"),
        },
        "rules": {
            "origin": Config.ORIGIN_ADDRESS,
            "max_radius_miles": Config.MAX_RADIUS_MILES,
            "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
            "food_only": True,
        },
        "data": filtered,
    })


@app.route("/api/debug/jobs")
def debug_jobs():
    result = fetch_jobs()
    enriched = [enrich_job_for_filters(job) for job in result["accepted"]]

    return jsonify({
        "status": "success",
        "source": VERSION,
        "accepted_count": len(enriched),
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
        "accepted": enriched,
        "rejected": result["rejected"],
    })


@app.route("/api/research/place")
def research_place():
    name = str_arg("name", "")
    place_id = str_arg("place_id", "")

    if not place_id and name:
        place = places_text_search(f"{name} Salt Lake City")
        place_id = clean((place or {}).get("place_id"))

    details = place_details(place_id) if place_id else {}
    search_results = web_search(f'"{name}" reviews chef employee restaurant Salt Lake City', 10) if name else []

    return jsonify({
        "status": "success",
        "name": name,
        "place_id": place_id,
        "place_details": details,
        "public_results": search_results,
    })


@app.route("/api/demo")
def demo():
    return jobs()

@app.route("/api/search", methods=["GET", "POST"])
def search():
    return jobs()


# === ORCHESTRATION_V1_START ===

from datetime import datetime, timezone, timedelta
from urllib.parse import quote as url_quote

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def batch_bucket() -> str:
    return os.environ.get("BATCH_BUCKET", "").strip()

def ingest_token() -> str:
    return os.environ.get("INGEST_TOKEN", "").strip()

def metadata_access_token() -> str:
    try:
        res = session.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"},
            timeout=5,
        )
        res.raise_for_status()
        return res.json().get("access_token", "")
    except Exception as exc:
        logger.warning("metadata token failed: %s", exc)
        return ""

def gcs_headers() -> Dict[str, str]:
    token = metadata_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

def gcs_upload_json(object_name: str, payload: Dict[str, Any]) -> bool:
    bucket = batch_bucket()
    if not bucket:
        return False

    try:
        url = f"https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o"
        res = session.post(
            url,
            params={
                "uploadType": "media",
                "name": object_name,
            },
            headers=gcs_headers(),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=30,
        )
        res.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("gcs upload failed %s: %s", object_name, exc)
        return False

def gcs_download_json(object_name: str) -> Dict[str, Any]:
    bucket = batch_bucket()
    if not bucket:
        return {}

    try:
        encoded = url_quote(object_name, safe="")
        url = f"https://storage.googleapis.com/storage/v1/b/{bucket}/o/{encoded}"
        res = session.get(
            url,
            params={"alt": "media"},
            headers=gcs_headers(),
            timeout=30,
        )
        res.raise_for_status()
        return res.json()
    except Exception as exc:
        logger.warning("gcs download failed %s: %s", object_name, exc)
        return {}

def gcs_list_batches(limit: int = 100) -> List[Dict[str, Any]]:
    bucket = batch_bucket()
    if not bucket:
        return []

    try:
        url = f"https://storage.googleapis.com/storage/v1/b/{bucket}/o"
        res = session.get(
            url,
            params={
                "prefix": "batches/",
                "maxResults": str(limit),
                "fields": "items(name,updated,size)",
            },
            headers=gcs_headers(),
            timeout=30,
        )
        res.raise_for_status()

        items = res.json().get("items", []) or []
        items = [i for i in items if i.get("name", "").endswith(".json")]
        items.sort(key=lambda x: x.get("updated", ""), reverse=True)
        return items
    except Exception as exc:
        logger.warning("gcs list failed: %s", exc)
        return []

@lru_cache(maxsize=1)
def serpapi_account_status_orchestration() -> Dict[str, Any]:
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

def budget_guard_allows_ingest() -> bool:
    reserve = int(os.environ.get("SERPAPI_MIN_SEARCHES_LEFT", "40"))
    account = serpapi_account_status_orchestration()
    left = account.get("total_searches_left")

    if left is None:
        return True

    try:
        return int(left) > reserve
    except Exception:
        return True

def serialize_ingest_batch() -> Dict[str, Any]:
    result = fetch_jobs()

    enriched = []
    if "enrich_job_for_filters" in globals():
        for job in result.get("accepted", []):
            try:
                enriched.append(enrich_job_for_filters(job))
            except Exception:
                enriched.append(job)
    else:
        enriched = result.get("accepted", [])

    return {
        "batch_schema": "job_hunter_batch_v1",
        "created_at_utc": utc_now_iso(),
        "source": VERSION if "VERSION" in globals() else "unknown",
        "rules": {
            "origin": Config.ORIGIN_ADDRESS,
            "max_radius_miles": Config.MAX_RADIUS_MILES,
            "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
            "food_only": True,
        },
        "budget": {
            "serpapi": serpapi_account_status_orchestration(),
            "max_serp_queries": Config.MAX_SERP_QUERIES,
            "max_raw_jobs": Config.MAX_RAW_JOBS,
            "max_ai_calls": Config.MAX_AI_CALLS,
        },
        "counts": {
            "accepted": len(enriched),
            "rejected": len(result.get("rejected", [])),
            "raw": result.get("raw_count"),
            "queries": result.get("query_count"),
            "nearby_restaurants": result.get("nearby_restaurant_count"),
        },
        "accepted": enriched,
        "rejected": result.get("rejected", []),
    }

@app.route("/api/usage")
def usage():
    return jsonify({
        "status": "ok",
        "serpapi": serpapi_account_status_orchestration(),
        "storage": {
            "batch_bucket": batch_bucket(),
            "bucket_configured": bool(batch_bucket()),
        },
        "orchestration": {
            "ingest_endpoint": "/api/ingest",
            "batches_endpoint": "/api/batches",
            "history_endpoint": "/api/history?hours=24",
            "recommended_scheduler": "every 6 hours while SerpAPI remaining searches are low",
            "budget_guard_min_searches_left": int(os.environ.get("SERPAPI_MIN_SEARCHES_LEFT", "40")),
        },
    })

@app.route("/api/ingest", methods=["GET", "POST"])
def ingest():
    token = request.args.get("token", "")

    if ingest_token() and token != ingest_token():
        return jsonify({
            "status": "error",
            "error": "invalid ingest token",
        }), 403

    if not budget_guard_allows_ingest():
        return jsonify({
            "status": "skipped",
            "reason": "serpapi_budget_guard",
            "serpapi": serpapi_account_status_orchestration(),
        }), 200

    batch = serialize_ingest_batch()
    dt = datetime.fromisoformat(batch["created_at_utc"])
    object_name = f"batches/{dt.strftime('%Y/%m/%d/%H%M%S')}_job_batch.json"

    ok = gcs_upload_json(object_name, batch)

    return jsonify({
        "status": "success" if ok else "error",
        "stored": ok,
        "object_name": object_name,
        "batch": {
            "created_at_utc": batch["created_at_utc"],
            "counts": batch["counts"],
            "source": batch["source"],
        },
    })

@app.route("/api/batches")
def batches():
    items = gcs_list_batches(200)

    return jsonify({
        "status": "success",
        "count": len(items),
        "bucket": batch_bucket(),
        "batches": [
            {
                "object_name": item.get("name"),
                "updated": item.get("updated"),
                "size": item.get("size"),
                "batch_id": item.get("name", "").replace("batches/", "").replace(".json", ""),
            }
            for item in items
        ],
    })

@app.route("/api/batch/<path:object_name>")
def batch_by_name(object_name):
    if not object_name.startswith("batches/"):
        object_name = "batches/" + object_name

    if not object_name.endswith(".json"):
        object_name += ".json"

    data = gcs_download_json(object_name)

    return jsonify({
        "status": "success" if data else "not_found",
        "object_name": object_name,
        "batch": data,
    })

@app.route("/api/history")
def history():
    hours_raw = request.args.get("hours", "24")

    try:
        hours = float(hours_raw)
    except Exception:
        hours = 24.0

    from_raw = request.args.get("from", "")
    to_raw = request.args.get("to", "")

    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(hours=hours)
    end_dt = now

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

        batch_summaries.append({
            "object_name": name,
            "created_at_utc": created_raw,
            "counts": data.get("counts"),
        })

        for job in data.get("accepted", []):
            j = dict(job)
            j["batch_object_name"] = name
            j["batch_created_at_utc"] = created_raw
            jobs_out.append(j)

    if "apply_user_filters" in globals():
        jobs_out = apply_user_filters(jobs_out)

    jobs_out.sort(key=lambda j: (
        j.get("batch_created_at_utc", ""),
        j.get("radius_miles") if j.get("radius_miles") is not None else 999,
    ), reverse=True)

    return jsonify({
        "status": "success",
        "source": "orchestration_batch_history_v1",
        "from": start_dt.isoformat(),
        "to": end_dt.isoformat(),
        "batch_count": len(batch_summaries),
        "job_count": len(jobs_out),
        "batches": batch_summaries,
        "data": jobs_out,
    })

# === ORCHESTRATION_V1_END ===



# === V7_ORCHESTRATION_DASHBOARD_START ===

from datetime import datetime, timezone, timedelta
from urllib.parse import quote as url_quote
import time

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def batch_bucket() -> str:
    return os.environ.get("BATCH_BUCKET", "").strip()

def ingest_token() -> str:
    return os.environ.get("INGEST_TOKEN", "").strip()

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
    bucket = batch_bucket()
    if not bucket:
        return False

    try:
        res = session.post(
            f"https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o",
            params={"uploadType": "media", "name": object_name},
            headers=gcs_headers(),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=30,
        )
        res.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("GCS upload failed: %s", exc)
        return False

def gcs_download_json(object_name: str) -> Dict[str, Any]:
    bucket = batch_bucket()
    if not bucket:
        return {}

    try:
        encoded = url_quote(object_name, safe="")
        res = session.get(
            f"https://storage.googleapis.com/storage/v1/b/{bucket}/o/{encoded}",
            params={"alt": "media"},
            headers=gcs_headers(),
            timeout=30,
        )
        res.raise_for_status()
        return res.json()
    except Exception:
        return {}

def gcs_list_batches(limit: int = 200) -> List[Dict[str, Any]]:
    bucket = batch_bucket()
    if not bucket:
        return []

    try:
        res = session.get(
            f"https://storage.googleapis.com/storage/v1/b/{bucket}/o",
            params={
                "prefix": "batches/",
                "maxResults": str(limit),
                "fields": "items(name,updated,size)",
            },
            headers=gcs_headers(),
            timeout=30,
        )
        res.raise_for_status()
        items = res.json().get("items", []) or []
        items = [i for i in items if i.get("name", "").endswith(".json")]
        items.sort(key=lambda x: x.get("updated", ""), reverse=True)
        return items
    except Exception as exc:
        logger.warning("GCS list failed: %s", exc)
        return []

def v7_place_details(place_id: str) -> Dict[str, Any]:
    place_id = clean(place_id)
    if not place_id or not Config.GOOGLE_MAPS_API_KEY:
        return {}

    try:
        res = session.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "name,rating,user_ratings_total,formatted_address,website,url,business_status,price_level,types",
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()
        return data.get("result") or {}
    except Exception:
        return {}

@lru_cache(maxsize=16)
def v7_nearby_opportunities(radius_miles: float = None) -> List[Dict[str, Any]]:
    origin = origin_latlng()
    if not origin or not Config.GOOGLE_MAPS_API_KEY:
        return []

    radius = radius_miles if radius_miles else Config.MAX_RADIUS_MILES
    keywords = ["restaurant", "cafe", "bakery", "bar", "diner", "grill", "coffee", "sandwich", "pizza"]
    seen = set()
    out = []

    for keyword in keywords:
        next_token = ""
        page_count = 0

        while True:
            params = {
                "location": f"{origin[0]},{origin[1]}",
                "radius": int(radius * 1609.344),
                "keyword": keyword,
                "key": Config.GOOGLE_MAPS_API_KEY,
            }

            if next_token:
                params = {
                    "pagetoken": next_token,
                    "key": Config.GOOGLE_MAPS_API_KEY,
                }
                time.sleep(2)

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
                radius_distance = None
                radius_label = "Radius unavailable"

                if "lat" in loc and "lng" in loc:
                    latlng = (float(loc["lat"]), float(loc["lng"]))
                    radius_distance = round(miles_between(origin, latlng), 2)
                    radius_label = f"{radius_distance} mi radius"

                details = v7_place_details(place_id)
                name = clean(details.get("name") or item.get("name"))
                address = clean(details.get("formatted_address") or item.get("vicinity"))

                out.append({
                    "type": "restaurant_opportunity",
                    "place_id": place_id,
                    "name": name,
                    "restaurant_name": name,
                    "resolved_address": address,
                    "radius_miles": radius_distance,
                    "radius_label": radius_label,
                    "google_rating": details.get("rating", item.get("rating")),
                    "google_review_count": details.get("user_ratings_total", item.get("user_ratings_total")),
                    "business_status": clean(details.get("business_status") or item.get("business_status")),
                    "website": clean(details.get("website")),
                    "google_maps_url": clean(details.get("url")),
                    "types": details.get("types") or item.get("types", []),
                    "suggested_searches": [
                        f'"{name}" server jobs',
                        f'"{name}" cook jobs',
                        f'"{name}" dishwasher jobs',
                        f'"{name}" host jobs',
                    ],
                })

            next_token = data.get("next_page_token") or ""
            page_count += 1
            if not next_token or page_count >= 3:
                break

    out.sort(key=lambda x: (
        x.get("radius_miles") if x.get("radius_miles") is not None else 999,
        -(float(x.get("google_rating") or 0)),
    ))

    return out[:160]

def v7_apply_opportunity_filters(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    min_rating = request.args.get("min_rating")
    max_radius = request.args.get("max_radius")
    q = clean(request.args.get("q", "")).lower()

    out = []

    for item in items:
        if min_rating:
            try:
                if float(item.get("google_rating") or 0) < float(min_rating):
                    continue
            except Exception:
                continue

        if max_radius:
            try:
                if float(item.get("radius_miles") or 999) > float(max_radius):
                    continue
            except Exception:
                continue

        if q:
            haystack = " ".join([
                clean(item.get("name")),
                clean(item.get("resolved_address")),
                " ".join(item.get("types") or []),
            ]).lower()
            if q not in haystack:
                continue

        out.append(item)

    return out

def serialize_ingest_batch() -> Dict[str, Any]:
    result = fetch_jobs()
    enriched = []

    for job in result.get("accepted", []):
        try:
            if "enrich_job_for_filters" in globals():
                enriched.append(enrich_job_for_filters(job))
            else:
                enriched.append(job)
        except Exception:
            enriched.append(job)

    return {
        "batch_schema": "job_hunter_batch_v1",
        "created_at_utc": utc_now_iso(),
        "source": VERSION if "VERSION" in globals() else "unknown",
        "rules": {
            "origin": Config.ORIGIN_ADDRESS,
            "max_radius_miles": Config.MAX_RADIUS_MILES,
            "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
            "food_only": True,
        },
        "budget": {
            "serpapi": serpapi_account_status(),
            "max_serp_queries": Config.MAX_SERP_QUERIES,
            "max_raw_jobs": Config.MAX_RAW_JOBS,
            "max_ai_calls": Config.MAX_AI_CALLS,
        },
        "counts": {
            "accepted": len(enriched),
            "rejected": len(result.get("rejected", [])),
            "raw": result.get("raw_count"),
            "queries": result.get("query_count"),
            "nearby_restaurants": result.get("nearby_restaurant_count"),
        },
        "accepted": enriched,
        "rejected": result.get("rejected", []),
    }

@app.route("/api/usage")
def usage():
    return jsonify({
        "status": "ok",
        "version": VERSION if "VERSION" in globals() else "unknown",
        "serpapi": serpapi_account_status(),
        "storage": {
            "batch_bucket": batch_bucket(),
            "bucket_configured": bool(batch_bucket()),
        },
        "budget": {
            "budget_mode": Config.SERPAPI_BUDGET_MODE,
            "min_searches_left_guard": Config.SERPAPI_MIN_SEARCHES_LEFT,
            "max_serp_queries_per_live_run": Config.MAX_SERP_QUERIES,
            "max_raw_jobs_per_live_run": Config.MAX_RAW_JOBS,
            "public_web_research_enabled": Config.ENABLE_PUBLIC_WEB_RESEARCH,
            "review_web_search_enabled": Config.ENABLE_REVIEW_WEB_SEARCH,
        },
        "orchestration": {
            "ingest_endpoint": "/api/ingest",
            "batches_endpoint": "/api/batches",
            "history_endpoint": "/api/history?hours=24",
            "opportunities_endpoint": "/api/opportunities",
            "why_three_endpoint": "/api/why-three",
        },
    })

@app.route("/api/why-three")
def why_three():
    return jsonify({
        "status": "explained",
        "why_only_few_jobs": [
            "The page is currently in SerpAPI budget mode.",
            "MAX_SERP_QUERIES is intentionally low to preserve your remaining SerpAPI searches.",
            "The visible jobs are strict accepted jobs, not all nearby restaurants.",
            "Strict filters require food-service match, exact or resolved place, radius, and transit pass.",
            "Historical accumulation requires /api/ingest batches over time, not only live page refreshes.",
            "Opportunities can show many nearby restaurants without spending SerpAPI job searches.",
        ],
        "current_limits": {
            "max_serp_queries": Config.MAX_SERP_QUERIES,
            "max_raw_jobs": Config.MAX_RAW_JOBS,
            "max_ai_calls": Config.MAX_AI_CALLS,
            "serpapi_min_searches_left_guard": Config.SERPAPI_MIN_SEARCHES_LEFT,
            "max_radius_miles": Config.MAX_RADIUS_MILES,
            "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
        },
        "next_correct_architecture": [
            "Use /api/opportunities for Google Places opportunity intelligence.",
            "Use /api/ingest every 6 hours while SerpAPI quota is low.",
            "Use /api/history for time-range browsing.",
            "Use /api/jobs only when intentionally burning a small live SerpAPI batch.",
        ],
    })

@app.route("/api/opportunities")
def opportunities():
    max_radius = request.args.get("max_radius")
    radius = None
    try:
        if max_radius:
            radius = float(max_radius)
    except Exception:
        radius = None

    data = v7_apply_opportunity_filters(v7_nearby_opportunities(radius))

    return jsonify({
        "status": "success",
        "source": "google_places_opportunities_no_serpapi",
        "count": len(data),
        "rules": {
            "origin": Config.ORIGIN_ADDRESS,
            "radius_miles": radius or Config.MAX_RADIUS_MILES,
            "uses_serpapi": False,
        },
        "data": data,
    })

@app.route("/api/ingest", methods=["GET", "POST"])
def ingest():
    token = request.args.get("token", "")

    if ingest_token() and token != ingest_token():
        return jsonify({"status": "error", "error": "invalid ingest token"}), 403

    account = serpapi_account_status()
    left = account.get("total_searches_left")

    if left is not None:
        try:
            if int(left) <= Config.SERPAPI_MIN_SEARCHES_LEFT:
                return jsonify({
                    "status": "skipped",
                    "reason": "serpapi_budget_guard",
                    "serpapi": account,
                })
        except Exception:
            pass

    batch = serialize_ingest_batch()
    created = datetime.fromisoformat(batch["created_at_utc"])
    object_name = f"batches/{created.strftime('%Y/%m/%d/%H%M%S')}_job_batch.json"
    ok = gcs_upload_json(object_name, batch)

    return jsonify({
        "status": "success" if ok else "error",
        "stored": ok,
        "object_name": object_name,
        "batch": {
            "created_at_utc": batch["created_at_utc"],
            "counts": batch["counts"],
            "source": batch["source"],
        },
    })

@app.route("/api/batches")
def batches():
    items = gcs_list_batches(200)
    return jsonify({
        "status": "success",
        "count": len(items),
        "bucket": batch_bucket(),
        "batches": [
            {
                "object_name": item.get("name"),
                "updated": item.get("updated"),
                "size": item.get("size"),
                "batch_id": item.get("name", "").replace("batches/", "").replace(".json", ""),
            }
            for item in items
        ],
    })

@app.route("/api/batch/<path:object_name>")
def batch_by_name(object_name):
    if not object_name.startswith("batches/"):
        object_name = "batches/" + object_name
    if not object_name.endswith(".json"):
        object_name += ".json"

    data = gcs_download_json(object_name)
    return jsonify({
        "status": "success" if data else "not_found",
        "object_name": object_name,
        "batch": data,
    })

@app.route("/api/history")
def history():
    hours_raw = request.args.get("hours", "24")
    try:
        hours = float(hours_raw)
    except Exception:
        hours = 24.0

    start_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    end_dt = datetime.now(timezone.utc)

    from_raw = request.args.get("from", "")
    to_raw = request.args.get("to", "")

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

        batch_summaries.append({
            "object_name": name,
            "created_at_utc": created_raw,
            "counts": data.get("counts"),
        })

        for job in data.get("accepted", []):
            j = dict(job)
            j["batch_object_name"] = name
            j["batch_created_at_utc"] = created_raw
            jobs_out.append(j)

    if "apply_user_filters" in globals():
        jobs_out = apply_user_filters(jobs_out)

    jobs_out.sort(key=lambda j: (
        j.get("batch_created_at_utc", ""),
        j.get("radius_miles") if j.get("radius_miles") is not None else 999,
    ), reverse=True)

    return jsonify({
        "status": "success",
        "source": "orchestration_batch_history_v1",
        "from": start_dt.isoformat(),
        "to": end_dt.isoformat(),
        "batch_count": len(batch_summaries),
        "job_count": len(jobs_out),
        "batches": batch_summaries,
        "data": jobs_out,
    })

# === V7_ORCHESTRATION_DASHBOARD_END ===


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
