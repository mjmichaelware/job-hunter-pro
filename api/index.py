import os, re, json, math, logging
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import requests
from flask import Flask, jsonify, request, render_template_string

BASE_DIR = Path(__file__).resolve().parent.parent
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("job-hunter-pro")

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
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
    MAX_SERP_QUERIES = int(os.environ.get("MAX_SERP_QUERIES", "14"))
    MAX_RAW_JOBS = int(os.environ.get("MAX_RAW_JOBS", "80"))
    MAX_AI_CALLS = int(os.environ.get("MAX_AI_CALLS", "20"))

ROLE_QUERIES = [
    "restaurant cook jobs near 84115 Salt Lake City",
    "line cook jobs near 84115 Salt Lake City",
    "prep cook jobs near 84115 Salt Lake City",
    "server jobs restaurant near 84115 Salt Lake City",
    "busser jobs restaurant near 84115 Salt Lake City",
    "host hostess restaurant jobs near 84115 Salt Lake City",
    "dishwasher restaurant jobs near 84115 Salt Lake City",
    "kitchen supervisor restaurant jobs near 84115 Salt Lake City",
    "food runner restaurant jobs near 84115 Salt Lake City",
    "barista cafe jobs near 84115 Salt Lake City",
]

FOOD_WORDS = [
    "restaurant","kitchen","cook","line cook","prep cook","server","busser","host","hostess",
    "dishwasher","dishwashing","food service","cafe","barista","crew member","cashier",
    "kitchen supervisor","shift lead","shift leader","expo","food runner","culinary","catering",
    "bakery","deli","chef","sous chef","grill","pizza","sandwich","dining","dish"
]

BAD_WORDS = [
    "software engineer","developer","nurse","warehouse","cdl","forklift","security guard",
    "mechanic","medical assistant","dental","rn","cna","teacher","account executive"
]

def clean(v: Any, fallback: str = "") -> str:
    if v is None:
        return fallback
    s = re.sub(r"\s+", " ", str(v)).strip()
    return s if s else fallback

def parse_jsonish(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text or "", re.S)
        if not m:
            return {}
        try:
            return json.loads(m.group(0))
        except Exception:
            return {}

def is_food_text(text: str) -> bool:
    t = clean(text).lower()
    if any(w in t for w in BAD_WORDS):
        return False
    return any(w in t for w in FOOD_WORDS)

def chef_names_from_text(text: str) -> List[str]:
    names = []
    for m in re.finditer(r"\b(?:chef|executive chef|sous chef)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})", text or ""):
        name = clean(m.group(1))
        if name and name not in names:
            names.append(name)
    return names[:5]

def miles_between(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    r = 3958.7613
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return 2 * r * math.asin(math.sqrt(h))

@lru_cache(maxsize=256)
def geocode(address: str) -> Optional[Tuple[float, float]]:
    if not Config.GOOGLE_MAPS_API_KEY or not clean(address):
        return None
    try:
        r = session.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": Config.GOOGLE_MAPS_API_KEY},
            timeout=Config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "OK" or not data.get("results"):
            return None
        loc = data["results"][0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])
    except Exception as e:
        logger.warning("geocode failed %s: %s", address, e)
        return None

def origin_latlng() -> Optional[Tuple[float, float]]:
    return geocode(Config.ORIGIN_ADDRESS)

@lru_cache(maxsize=1)
def nearby_restaurants() -> List[Dict[str, Any]]:
    origin = origin_latlng()
    if not origin or not Config.GOOGLE_MAPS_API_KEY:
        return []
    try:
        r = session.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "location": f"{origin[0]},{origin[1]}",
                "radius": int(Config.MAX_RADIUS_MILES * 1609.344),
                "type": "restaurant",
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
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
    except Exception as e:
        logger.warning("nearby restaurants failed: %s", e)
        return []

@lru_cache(maxsize=512)
def places_text_search(query: str) -> Optional[Dict[str, Any]]:
    query = clean(query)
    origin = origin_latlng()
    if not query or not origin or not Config.GOOGLE_MAPS_API_KEY:
        return None
    try:
        r = session.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={
                "query": query,
                "location": f"{origin[0]},{origin[1]}",
                "radius": int(max(Config.MAX_RADIUS_MILES, 3.0) * 1609.344),
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
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
    except Exception as e:
        logger.warning("places search failed %s: %s", query, e)
        return None

@lru_cache(maxsize=512)
def transit_to(destination: str) -> Dict[str, Any]:
    destination = clean(destination)
    empty = {"commute_seconds": None, "commute_label": "Transit unavailable", "transit_distance_miles": None, "transit_distance_label": "Transit distance unavailable"}
    if not destination or not Config.GOOGLE_MAPS_API_KEY:
        return empty
    try:
        r = session.get(
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
        r.raise_for_status()
        data = r.json()
        el = data.get("rows", [{}])[0].get("elements", [{}])[0]
        if el.get("status") != "OK":
            return empty
        sec = int(el["duration"]["value"])
        mi = int(el["distance"]["value"]) / 1609.344
        return {"commute_seconds": sec, "commute_label": f"{round(sec/60)}m transit", "transit_distance_miles": round(mi, 2), "transit_distance_label": f"{round(mi, 2)} mi transit route"}
    except Exception as e:
        logger.warning("transit failed %s: %s", destination, e)
        return empty

def serpapi_jobs(query: str) -> List[Dict[str, Any]]:
    if not Config.SERPAPI_KEY:
        return []
    try:
        r = session.get(
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
        r.raise_for_status()
        return r.json().get("jobs_results", []) or []
    except Exception as e:
        logger.warning("serpapi failed %s: %s", query, e)
        return []

def ai_prompt(raw: Dict[str, Any]) -> str:
    return f"""Return ONLY compact JSON for this job listing.
Keys:
restaurant_name string|null
role string|null
chef_names array
is_food_service boolean
google_place_queries array of 1-5 strings

Goal: identify the real restaurant/cafe/bar/bakery location. Do not invent street addresses. Use Google Maps style search queries near 84115 Salt Lake City.

Title: {clean(raw.get("title"))}
Company: {clean(raw.get("company_name") or raw.get("company"))}
Location: {clean(raw.get("location"))}
Description: {clean(raw.get("description"))[:1500]}
"""

def openai_like_extract(provider: str, key: str, base: str, model: str, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not key:
        return None
    try:
        r = session.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": "You extract factual restaurant job entities. Return JSON only."},
                    {"role": "user", "content": ai_prompt(raw)},
                ],
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        data = parse_jsonish(text)
        if data:
            data["_provider"] = provider
            return data
    except Exception as e:
        logger.warning("%s AI failed: %s", provider, e)
    return None

def gemini_extract(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not Config.GEMINI_API_KEY:
        return None
    try:
        r = session.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
            params={"key": Config.GEMINI_API_KEY},
            json={
                "contents": [{"parts": [{"text": ai_prompt(raw)}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        data = parse_jsonish(text)
        if data:
            data["_provider"] = "gemini"
            return data
    except Exception as e:
        logger.warning("gemini AI failed: %s", e)
    return None

def anthropic_extract(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not Config.ANTHROPIC_API_KEY:
        return None
    try:
        r = session.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": Config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json={
                "model": "claude-3-5-haiku-latest",
                "max_tokens": 600,
                "temperature": 0,
                "messages": [{"role": "user", "content": ai_prompt(raw)}],
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        text = "".join(x.get("text", "") for x in r.json().get("content", []) if x.get("type") == "text")
        data = parse_jsonish(text)
        if data:
            data["_provider"] = "claude"
            return data
    except Exception as e:
        logger.warning("claude AI failed: %s", e)
    return None

AI_CALL_COUNT = 0

def deterministic_extract(raw: Dict[str, Any]) -> Dict[str, Any]:
    title = clean(raw.get("title"))
    company = clean(raw.get("company_name") or raw.get("company"))
    location = clean(raw.get("location"))
    desc = clean(raw.get("description"))
    text = " ".join([title, company, location, desc])
    queries = []
    for q in [
        f"{company} restaurant near 84115 Salt Lake City UT",
        f"{company} cafe near 84115 Salt Lake City UT",
        f"{company} {title} near 84115 Salt Lake City UT",
    ]:
        q = clean(q)
        if company and q not in queries:
            queries.append(q)
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

    for fn in providers:
        AI_CALL_COUNT += 1
        data = fn()
        if data and data.get("google_place_queries"):
            return data

    return base

def resolve_place(raw: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
    queries = []
    for q in ai.get("google_place_queries", []) or []:
        q = clean(q)
        if q and q not in queries:
            queries.append(q)

    company = clean(raw.get("company_name") or raw.get("company"))
    title = clean(raw.get("title"))
    for q in [
        f"{company} restaurant near 84115 Salt Lake City UT",
        f"{company} {title} near 84115 Salt Lake City UT",
        f"{company} near 84115 Salt Lake City UT",
    ]:
        q = clean(q)
        if company and q not in queries:
            queries.append(q)

    for q in queries[:8]:
        place = places_text_search(q)
        if place and place.get("formatted_address") and place.get("latlng"):
            return place

    return {"name": "", "formatted_address": "", "place_id": "", "rating": None, "types": [], "latlng": None, "query_used": ""}

def salary(raw: Dict[str, Any]) -> str:
    d = raw.get("detected_extensions") or {}
    if d.get("salary"):
        return clean(d.get("salary"))
    if raw.get("salary"):
        return clean(raw.get("salary"))
    ex = raw.get("extensions")
    if isinstance(ex, list):
        for x in ex:
            x = clean(x)
            if "$" in x or "/hr" in x.lower() or "hour" in x.lower():
                return x
    return "Salary not listed"

def apply_link(raw: Dict[str, Any]) -> str:
    opts = raw.get("apply_options")
    if isinstance(opts, list) and opts:
        first = opts[0]
        if isinstance(first, dict):
            return clean(first.get("link"))
    return ""

def tags_for(job: Dict[str, Any]) -> List[str]:
    t = " ".join([clean(job.get("title")), clean(job.get("description")), clean(job.get("company")), clean(job.get("restaurant_name"))]).lower()
    rules = [
        ("line-cook", ["line cook"]),
        ("prep-cook", ["prep cook"]),
        ("server", ["server"]),
        ("busser", ["busser"]),
        ("host-hostess", ["host", "hostess"]),
        ("dishwasher", ["dishwasher"]),
        ("kitchen", ["kitchen", "cook", "chef"]),
        ("barista", ["barista", "coffee", "cafe"]),
        ("supervisor", ["supervisor", "shift lead", "shift leader"]),
        ("restaurant", ["restaurant", "dining"]),
    ]
    out = []
    for tag, words in rules:
        if any(w in t for w in words):
            out.append(tag)
    return out[:5] or ["food-service"]

def match_score(job: Dict[str, Any]) -> int:
    score = 70
    t = " ".join([clean(job.get("title")), clean(job.get("description")), clean(job.get("restaurant_name"))]).lower()
    for word, pts in {"line cook":10,"prep cook":10,"cook":8,"server":7,"busser":7,"host":6,"dishwasher":6,"chef":6,"restaurant":7,"kitchen":8}.items():
        if word in t:
            score += pts
    c = job.get("commute_seconds")
    r = job.get("radius_miles")
    if c is not None:
        score += 10 if c <= 900 else 7 if c <= 1500 else 3 if c < Config.MAX_TRANSIT_SECONDS else -10
    if r is not None:
        score += 10 if r <= 1 else 6 if r <= 2 else 3 if r <= Config.MAX_RADIUS_MILES else -10
    if job.get("resolved_address"):
        score += 5
    return max(1, min(score, 99))

def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    ai = ai_extract(raw)
    place = resolve_place(raw, ai)

    title = clean(raw.get("title"), "Untitled Restaurant Role")
    company = clean(raw.get("company_name") or raw.get("company"), "Company not listed")
    listing_location = clean(raw.get("location"), Config.JOB_LOCATION)
    desc = clean(raw.get("description"), "No description available.")

    resolved_address = clean(place.get("formatted_address"))
    resolved_name = clean(place.get("name"))
    destination = resolved_address or listing_location
    transit = transit_to(destination)

    radius = None
    radius_label = "Radius unavailable"
    origin = origin_latlng()
    if origin and place.get("latlng"):
        radius = round(miles_between(origin, place["latlng"]), 2)
        radius_label = f"{radius} mi radius"

    job = {
        "title": title,
        "company": company,
        "restaurant_name": ai.get("restaurant_name") or resolved_name or company,
        "resolved_place_name": resolved_name,
        "resolved_address": resolved_address,
        "location": resolved_address or listing_location,
        "listing_location": listing_location,
        "salary": salary(raw),
        "description": desc,
        "commute_seconds": transit["commute_seconds"],
        "commute_label": transit["commute_label"],
        "radius_miles": radius,
        "radius_label": radius_label,
        "distance_miles": radius,
        "distance_label": radius_label,
        "transit_distance_miles": transit["transit_distance_miles"],
        "transit_distance_label": transit["transit_distance_label"],
        "source_url": apply_link(raw),
        "job_id": clean(raw.get("job_id")),
        "via": clean(raw.get("via")),
        "ai_provider": ai.get("_provider"),
        "chef_names": ai.get("chef_names") or chef_names_from_text(desc),
        "place_query_used": place.get("query_used"),
        "place_id": place.get("place_id"),
        "place_rating": place.get("rating"),
    }
    job["tags"] = tags_for(job)
    job["match"] = match_score(job)
    return job

def rejection_reasons(job: Dict[str, Any]) -> List[str]:
    reasons = []
    if not is_food_text(" ".join([clean(job.get("title")), clean(job.get("company")), clean(job.get("description")), clean(job.get("restaurant_name")), clean(job.get("resolved_place_name"))])):
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
        reasons.append(f"transit_too_long_{round(job['commute_seconds']/60)}min")
    return reasons

def raw_job_queries() -> List[str]:
    queries = list(ROLE_QUERIES)
    for r in nearby_restaurants()[:8]:
        name = clean(r.get("name"))
        if name:
            queries.append(f'"{name}" restaurant jobs Salt Lake City')
            queries.append(f'"{name}" cook server dishwasher jobs')
    unique = []
    for q in queries:
        if q not in unique:
            unique.append(q)
    return unique[:Config.MAX_SERP_QUERIES]

@lru_cache(maxsize=8)
def fetch_jobs_cached(debug_key: str = "normal") -> Dict[str, Any]:
    seen = set()
    raw_all = []

    for q in raw_job_queries():
        for raw in serpapi_jobs(q):
            ident = clean(raw.get("job_id")) or clean(raw.get("title")) + clean(raw.get("company_name")) + clean(raw.get("location"))
            if ident and ident not in seen:
                seen.add(ident)
                raw["_query_used"] = q
                raw_all.append(raw)
            if len(raw_all) >= Config.MAX_RAW_JOBS:
                break
        if len(raw_all) >= Config.MAX_RAW_JOBS:
            break

    accepted, rejected = [], []

    for raw in raw_all:
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

    accepted.sort(key=lambda j: (j.get("radius_miles") if j.get("radius_miles") is not None else 999, j.get("commute_seconds") if j.get("commute_seconds") is not None else 999999, -j.get("match", 0)))

    return {
        "raw_count": len(raw_all),
        "query_count": len(raw_job_queries()),
        "nearby_restaurant_count": len(nearby_restaurants()),
        "accepted": accepted[:25],
        "rejected": rejected[:80],
    }

@app.after_request
def headers(resp):
    resp.headers["X-App-Name"] = "job-hunter-pro"
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.route("/")
def index():
    return render_template_string("""
<!doctype html><html><head><meta charset="utf-8"><title>Job Hunter Pro</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/static/css/main.css"></head>
<body><main class="container section">
<p class="kicker">Cloud Run Online</p>
<h1 class="text-gradient">Job Hunter Pro</h1>
<p class="lead">Live restaurant jobs resolved through AI + Google Places, then filtered by 2.5 mile radius and under 35 min transit.</p>
<div class="cluster"><a class="btn btn-primary" href="/api/health">Health</a><button class="btn btn-ghost" onclick="loadJobs()">Refresh Restaurant Jobs</button><a class="btn btn-ghost" href="/api/debug/jobs">Debug</a></div>
<p class="status-line" id="status">Loading live jobs...</p><section class="grid-system" id="jobs"></section>
</main><div class="noise"></div><script src="/static/js/main.js"></script>
<script>
function loadJobs(){const s=document.getElementById('status');s.textContent='Searching live jobs with AI + Google Places...';fetch('/api/jobs').then(r=>r.json()).then(p=>{s.textContent=`Showing ${p.count||0} strict-matched jobs. Raw scanned: ${p.raw_count||0}. Nearby restaurants: ${p.nearby_restaurant_count||0}.`;window.UI&&window.UI.renderJobs(p.data||[])}).catch(e=>{console.error(e);s.textContent='Search failed. Open Debug.'})}
loadJobs();
</script></body></html>
""")

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "version": "ai_places_resolver_v1",
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
        "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS/60),
        "nearby_restaurant_count": len(nearby_restaurants()),
        "pipeline": ["Google Places nearby restaurants", "SerpAPI Google Jobs", "LLM entity extraction fallback", "Google Places Text Search", "Google Distance Matrix", "strict radius/transit filter"],
    })

@app.route("/api/ai/status")
def ai_status():
    return health()

@app.route("/api/jobs")
def jobs():
    result = fetch_jobs_cached("normal")
    return jsonify({
        "status": "success",
        "source": "ai_places_resolver_v1",
        "count": len(result["accepted"]),
        "raw_count": result["raw_count"],
        "query_count": result["query_count"],
        "nearby_restaurant_count": result["nearby_restaurant_count"],
        "rules": {"origin": Config.ORIGIN_ADDRESS, "max_radius_miles": Config.MAX_RADIUS_MILES, "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS/60), "food_only": True},
        "data": result["accepted"],
    })

@app.route("/api/debug/jobs")
def debug_jobs():
    result = fetch_jobs_cached("debug")
    return jsonify({
        "status": "success",
        "source": "ai_places_resolver_v1",
        "accepted_count": len(result["accepted"]),
        "rejected_count": len(result["rejected"]),
        "raw_count": result["raw_count"],
        "query_count": result["query_count"],
        "nearby_restaurant_count": result["nearby_restaurant_count"],
        "rules": {"origin": Config.ORIGIN_ADDRESS, "max_radius_miles": Config.MAX_RADIUS_MILES, "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS/60), "food_only": True},
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
