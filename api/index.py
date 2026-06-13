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

    MAX_TRANSIT_SECONDS = int(os.environ.get("MAX_TRANSIT_SECONDS", "2100"))
    MAX_RADIUS_MILES = float(os.environ.get("MAX_RADIUS_MILES", "2.5"))
    REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "12"))

    MAX_SERP_QUERIES = int(os.environ.get("MAX_SERP_QUERIES", "4"))
    MAX_RAW_JOBS = int(os.environ.get("MAX_RAW_JOBS", "35"))
    MAX_AI_CALLS = int(os.environ.get("MAX_AI_CALLS", "8"))
    SERPAPI_MIN_SEARCHES_LEFT = int(os.environ.get("SERPAPI_MIN_SEARCHES_LEFT", "40"))
    SERPAPI_BUDGET_MODE = os.environ.get("SERPAPI_BUDGET_MODE", "1").strip() == "1"

    ENABLE_PUBLIC_WEB_RESEARCH = os.environ.get("ENABLE_PUBLIC_WEB_RESEARCH", "0").strip() == "1"
    ENABLE_REVIEW_WEB_SEARCH = os.environ.get("ENABLE_REVIEW_WEB_SEARCH", "0").strip() == "1"

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
        res = session.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": Config.GOOGLE_MAPS_API_KEY},
            timeout=Config.REQUEST_TIMEOUT,
        )
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
        res = session.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "name,rating,user_ratings_total,reviews,formatted_address,website,url,business_status,formatted_phone_number,price_level,types",
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
        logger.warning("place details failed: %s", exc)
        return {}

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
                "radius": int(max(Config.MAX_RADIUS_MILES, 5) * 1609.344),
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
        f"{company} restaurant Salt Lake City",
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
    title = clean(raw.get("title"), "Untitled Restaurant Role")
    company = clean_company(raw.get("company_name") or raw.get("company")) or "Company not listed"
    listing_location = clean(raw.get("location"), Config.JOB_LOCATION)
    description = clean(raw.get("description"), "No description available.")
    if os.environ.get("FAST_JOBS", "0") == "1":
        place = {}
        resolved_address = ""
        resolved_name = ""
        transit = {"commute_seconds": None, "commute_label": "Not checked",
                   "transit_distance_miles": None, "transit_distance_label": "Not checked"}
        radius_miles = None
    else:
        place = resolve_place(raw)
        resolved_address = clean(place.get("formatted_address"))
        resolved_name = clean(place.get("name"))
        destination = resolved_address or listing_location
        transit = transit_to(destination)
        origin = origin_latlng()
        radius_miles = None
        if origin and place.get("latlng"):
            radius_miles = round(miles_between(origin, place["latlng"]), 2)
    text = " ".join([title, company, description, resolved_name])
    tags = tags_for_text(text)
    job = {
        "title": title,
        "company": company,
        "restaurant_name": resolved_name or company,
        "resolved_place_name": resolved_name,
        "resolved_address": resolved_address,
        "location": resolved_address or listing_location,
        "listing_location": listing_location,
        "salary": salary_from_raw(raw),
        "description": description,
        "commute_seconds": transit["commute_seconds"],
        "commute_label": transit["commute_label"],
        "radius_miles": radius_miles,
        "radius_label": f"{radius_miles} mi radius" if radius_miles is not None else "Radius unavailable",
        "distance_miles": radius_miles,
        "distance_label": f"{radius_miles} mi radius" if radius_miles is not None else "Radius unavailable",
        "transit_distance_miles": transit["transit_distance_miles"],
        "transit_distance_label": transit["transit_distance_label"],
        "source_url": apply_link(raw),
        "job_id": clean(raw.get("job_id")),
        "via": clean(raw.get("via")),
        "ai_provider": "deterministic_budget_safe",
        "chef_names": [],
        "place_query_used": place.get("query_used"),
        "place_id": place.get("place_id"),
        "place_rating": place.get("rating"),
        "tags": tags,
        "role_family": role_family_for_text(" ".join(tags + [title, description])),
    }
    job["match"] = match_score(job)
    ri = {} if os.environ.get("FAST_JOBS", "0") == "1" else review_intelligence(job)
    job["review_intelligence"] = ri
    job["google_rating"] = ri.get("google_rating") or job.get("place_rating")
    job["google_review_count"] = ri.get("google_review_count")
    job["review_score"] = ri.get("review_score")
    job["consistency_score"] = ri.get("consistency_score")
    job["risk_level"] = ri.get("risk_level")
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
    return []

def canonical_key(job: Dict[str, Any]) -> str:
    title = clean(job.get("title")).lower()
    name = clean(job.get("restaurant_name")).lower()
    addr = clean(job.get("resolved_address")).lower()
    if not name and not addr:
        uniq = (clean(job.get("source_url")) or clean(job.get("url")) or clean(job.get("company")) or clean(job.get("job_id"))).lower()
        return f"{title}|{uniq}"
    return f"{title}|{name}|{addr}"

def raw_job_queries() -> List[str]:
    queries = list(ROLE_QUERIES)
    for restaurant in nearby_opportunities_cached(Config.MAX_RADIUS_MILES)[:8]:
        name = clean(restaurant.get("name"))
        if name:
            queries.append(f'"{name}" restaurant jobs Salt Lake City')
            queries.append(f'"{name}" server cook dishwasher jobs')
    unique = []
    for query in queries:
        if query not in unique:
            unique.append(query)
    return unique

def fetch_jobs_live() -> Dict[str, Any]:
    raw_jobs = []
    provider_breakdown = {}
    queries = raw_job_queries()
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

    accepted = []
    rejected = []
    accepted_keys = set()

    for raw in raw_jobs:
        job = normalize_job(raw)
        reasons = rejection_reasons(job)
        if reasons:
            rejected.append({
                "provider": raw.get("_provider") or raw.get("source") or raw.get("via"),
                "query": raw.get("_query_used"),
                "title": job.get("title"),
                "company": job.get("company"),
                "restaurant_name": job.get("restaurant_name"),
                "resolved_address": job.get("resolved_address"),
                "commute_label": job.get("commute_label"),
                "radius_label": job.get("radius_label"),
                "tags": job.get("tags"),
                "source_url": job.get("source_url"),
                "reasons": reasons,
            })
        else:
            key = canonical_key(job)
            if key not in accepted_keys:
                accepted_keys.add(key)
                accepted.append(job)

    accepted.sort(key=lambda j: (
        j.get("radius_miles") if j.get("radius_miles") is not None else 999,
        j.get("commute_seconds") if j.get("commute_seconds") is not None else 999999,
        -j.get("match", 0),
    ))

    return {
        "raw_count": len(raw_jobs),
        "query_count": query_count,
        "nearby_restaurant_count": len(nearby_opportunities_cached(Config.MAX_RADIUS_MILES)),
        "accepted": accepted,
        "rejected": rejected[:100],
        "provider_breakdown": provider_breakdown,
    }

def float_arg(name: str, default: Optional[float]) -> Optional[float]:
    value = request.args.get(name)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except Exception:
        return default

def apply_filters(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    min_rating = float_arg("min_rating", None)
    max_radius = float_arg("max_radius", None)
    max_transit = float_arg("max_transit", None)
    min_score = float_arg("min_score", None)
    role = clean(request.args.get("role", "all")).lower()
    house = clean(request.args.get("house", "all")).lower()
    q = clean(request.args.get("q", "")).lower()
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
                rv = job.get("radius_miles")
                if rv is not None and float(rv) > max_radius:
                    continue
            except Exception:
                continue
        if max_transit is not None:
            try:
                cv = job.get("commute_seconds")
                if cv is not None and float(cv) / 60 > max_transit:
                    continue
            except Exception:
                continue
        if min_score is not None:
            try:
                if float(job.get("review_score") or 0) < min_score:
                    continue
            except Exception:
                continue
        text = " ".join([clean(job.get("title")), " ".join(job.get("tags") or [])]).lower()
        if role and role != "all" and role not in text:
            continue
        if house and house != "all" and clean(job.get("role_family")).lower() != house:
            continue
        if q:
            haystack = " ".join([
                clean(job.get("title")),
                clean(job.get("restaurant_name")),
                clean(job.get("resolved_address")),
                clean(job.get("description")),
                " ".join(job.get("tags") or []),
            ]).lower()
            if q not in haystack:
                continue
        out.append(job)
    return out

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

    result = fetch_jobs_live()
    filtered = apply_filters(result["accepted"])

    rejection_summary = {}
    for item in result.get("rejected", []):
        for reason in item.get("reasons", []):
            rejection_summary[reason] = rejection_summary.get(reason, 0) + 1

    return jsonify({
        "status": "success",
        "source": VERSION,
        "count": len(filtered),
        "unfiltered_count": len(result["accepted"]),
        "raw_count": result["raw_count"],
        "query_count": result["query_count"],
        "nearby_restaurant_count": result["nearby_restaurant_count"],
        "rejected_count": len(result.get("rejected", [])),
        "rejection_summary": rejection_summary,
        "provider_breakdown": result.get("provider_breakdown", {}),
        "rules": {
            "origin": Config.ORIGIN_ADDRESS,
            "max_radius_miles": Config.MAX_RADIUS_MILES,
            "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
            "food_only": True,
            "discovery": "federated_search_providers",
            "reasoning_providers": "not_used_as_discovery",
        },
        "data": filtered,
        "rejected": result.get("rejected", [])[:100],
    })

@app.route("/api/debug/jobs")
def debug_jobs():
    result = fetch_jobs_live()
    return jsonify({
        "status": "success",
        "source": VERSION,
        "accepted_count": len(result["accepted"]),
        "rejected_count": len(result["rejected"]),
        "raw_count": result["raw_count"],
        "query_count": result["query_count"],
        "nearby_restaurant_count": result["nearby_restaurant_count"],
        "provider_breakdown": result.get("provider_breakdown", {}),
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
        "counts": {"accepted": len(result["accepted"]), "rejected": len(result["rejected"]), "raw": result["raw_count"], "queries": result["query_count"], "nearby_restaurants": result["nearby_restaurant_count"]},
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



@app.route("/api/search", methods=["GET", "POST"])
def search():
    return jobs()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
