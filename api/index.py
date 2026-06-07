import os
import re
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

class Config:
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

    ORIGIN_ADDRESS = os.environ.get(
        "ORIGIN_ADDRESS",
        "28 E Bryan Ave, Salt Lake City, UT 84115"
    ).strip()

    JOB_LOCATION = os.environ.get(
        "JOB_LOCATION",
        "84115"
    ).strip()

    MAX_TRANSIT_SECONDS = int(os.environ.get("MAX_TRANSIT_SECONDS", "2100"))
    MAX_RADIUS_MILES = float(os.environ.get("MAX_RADIUS_MILES", "2.5"))
    REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "12"))

    JOB_QUERIES = [
        "restaurant cook jobs",
        "line cook jobs",
        "prep cook jobs",
        "server restaurant jobs",
        "busser restaurant jobs",
        "host hostess restaurant jobs",
        "dishwasher restaurant jobs",
        "kitchen supervisor restaurant jobs",
        "food service jobs",
        "barista cafe jobs",
    ]

session = requests.Session()

FOOD_KEYWORDS = [
    "restaurant", "kitchen", "cook", "line cook", "prep cook", "server",
    "busser", "bussers", "host", "hostess", "dishwasher", "dishwashing",
    "food service", "cafe", "barista", "crew member", "cashier",
    "kitchen supervisor", "shift lead", "shift leader", "expo",
    "food runner", "culinary", "catering", "bakery", "deli"
]

BLOCK_KEYWORDS = [
    "software", "engineer", "developer", "nurse", "driver", "warehouse",
    "sales representative", "account executive", "security guard",
    "teacher", "mechanic", "medical assistant", "dental", "rn", "cna"
]

def clean_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text if text else fallback

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
    address = clean_text(address)
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
            logger.warning("Geocode failed for %s: %s", address, data.get("status"))
            return None

        loc = data["results"][0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])

    except Exception as exc:
        logger.exception("Geocode error for %s: %s", address, exc)
        return None

@lru_cache(maxsize=512)
def get_commute(destination: str) -> Dict[str, Any]:
    destination = clean_text(destination)
    empty = {
        "commute_seconds": None,
        "commute_label": "Commute unavailable",
        "distance_miles": None,
        "distance_label": "Distance unavailable",
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
            logger.warning("Distance Matrix failed for %s: %s", destination, element.get("status"))
            return empty

        seconds = int(element["duration"]["value"])
        meters = int(element["distance"]["value"])
        miles = meters / 1609.344

        return {
            "commute_seconds": seconds,
            "commute_label": f"{round(seconds / 60)}m transit",
            "distance_miles": round(miles, 2),
            "distance_label": f"{round(miles, 2)} mi",
        }

    except Exception as exc:
        logger.exception("Commute error for %s: %s", destination, exc)
        return empty

def is_food_job(job: Dict[str, Any]) -> bool:
    text = " ".join([
        clean_text(job.get("title")),
        clean_text(job.get("company")),
        clean_text(job.get("location")),
        clean_text(job.get("description")),
    ]).lower()

    if any(block in text for block in BLOCK_KEYWORDS):
        return False

    return any(keyword in text for keyword in FOOD_KEYWORDS)

def infer_tags(job: Dict[str, Any]) -> List[str]:
    text = " ".join([
        clean_text(job.get("title")),
        clean_text(job.get("description")),
        clean_text(job.get("company")),
    ]).lower()

    tags = []

    rules = [
        ("restaurant", ["restaurant", "server", "busser", "host", "hostess"]),
        ("kitchen", ["kitchen", "cook", "dishwasher", "culinary"]),
        ("line-cook", ["line cook"]),
        ("prep-cook", ["prep cook"]),
        ("server", ["server"]),
        ("busser", ["busser", "bussers"]),
        ("host-hostess", ["host", "hostess"]),
        ("dishwasher", ["dishwasher", "dishwashing"]),
        ("supervisor", ["supervisor", "shift lead", "shift leader"]),
        ("barista", ["barista", "cafe", "coffee"]),
    ]

    for tag, keywords in rules:
        if any(keyword in text for keyword in keywords):
            tags.append(tag)

    return tags[:5] or ["food-service"]

def calculate_match(job: Dict[str, Any]) -> int:
    score = 70
    text = " ".join([
        clean_text(job.get("title")),
        clean_text(job.get("description")),
        clean_text(job.get("company")),
    ]).lower()

    boost_terms = {
        "cook": 8,
        "prep": 8,
        "line cook": 10,
        "server": 7,
        "busser": 7,
        "host": 6,
        "hostess": 6,
        "dishwasher": 6,
        "restaurant": 8,
        "kitchen": 8,
        "supervisor": 5,
        "food service": 8,
        "barista": 5,
    }

    for term, points in boost_terms.items():
        if term in text:
            score += points

    commute = job.get("commute_seconds")
    distance = job.get("distance_miles")

    if commute is not None:
        if commute <= 900:
            score += 10
        elif commute <= 1500:
            score += 7
        elif commute < Config.MAX_TRANSIT_SECONDS:
            score += 3

    if distance is not None:
        if distance <= 1:
            score += 10
        elif distance <= 2:
            score += 6
        elif distance <= Config.MAX_RADIUS_MILES:
            score += 3

    return max(1, min(score, 99))

def normalize_serp_job(raw: Dict[str, Any]) -> Dict[str, Any]:
    detected_extensions = raw.get("detected_extensions") or {}

    title = clean_text(raw.get("title"), "Untitled Restaurant Role")
    company = clean_text(raw.get("company_name"), "Company not listed")
    location = clean_text(raw.get("location"), Config.JOB_LOCATION)
    description = clean_text(raw.get("description"), "No description available.")
    salary = clean_text(
        detected_extensions.get("salary")
        or raw.get("salary")
        or raw.get("extensions", [""])[0] if raw.get("extensions") else "",
        "Salary not listed"
    )

    commute = get_commute(location)

    job = {
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "description": description,
        "commute_seconds": commute["commute_seconds"],
        "commute_label": commute["commute_label"],
        "distance_miles": commute["distance_miles"],
        "distance_label": commute["distance_label"],
        "tags": [],
        "match": 0,
        "source_url": "",
        "apply_options": raw.get("apply_options", []),
        "via": clean_text(raw.get("via")),
        "job_id": clean_text(raw.get("job_id")),
    }

    if job["apply_options"]:
        first = job["apply_options"][0]
        if isinstance(first, dict):
            job["source_url"] = clean_text(first.get("link"))

    job["tags"] = infer_tags(job)
    job["match"] = calculate_match(job)

    return job

def passes_location_rules(job: Dict[str, Any]) -> bool:
    commute = job.get("commute_seconds")
    distance = job.get("distance_miles")

    if commute is None or distance is None:
        return False

    return commute < Config.MAX_TRANSIT_SECONDS and distance <= Config.MAX_RADIUS_MILES

def fetch_serpapi_jobs() -> List[Dict[str, Any]]:
    if not Config.SERPAPI_KEY:
        return []

    seen = set()
    jobs = []

    for query in Config.JOB_QUERIES:
        try:
            res = session.get(
                "https://serpapi.com/search.json",
                params={
                    "engine": "google_jobs",
                    "q": query,
                    "location": Config.JOB_LOCATION,
                    "hl": "en",
                    "gl": "us",
                    "api_key": Config.SERPAPI_KEY,
                },
                timeout=Config.REQUEST_TIMEOUT,
            )
            res.raise_for_status()
            data = res.json()

            for raw in data.get("jobs_results", []) or []:
                job_id = clean_text(raw.get("job_id")) or clean_text(raw.get("title")) + clean_text(raw.get("company_name")) + clean_text(raw.get("location"))

                if job_id in seen:
                    continue

                seen.add(job_id)
                normalized = normalize_serp_job(raw)

                if is_food_job(normalized) and passes_location_rules(normalized):
                    jobs.append(normalized)

        except Exception as exc:
            logger.exception("SerpAPI query failed for %s: %s", query, exc)

    jobs.sort(key=lambda job: (
        job["distance_miles"] if job["distance_miles"] is not None else 999,
        job["commute_seconds"] if job["commute_seconds"] is not None else 999999,
        -job["match"],
    ))

    return jobs[:25]

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
  <main class="container section">
    <p class="kicker">Cloud Run Online</p>
    <h1 class="text-gradient">Job Hunter Pro</h1>
    <p class="lead">Live restaurant jobs filtered by transit time and 2.5 mile radius from your 84115 origin.</p>
    <div class="cluster">
      <a class="btn btn-primary" href="/api/health">Health Check</a>
      <button class="btn btn-ghost" onclick="loadJobs()">Refresh Restaurant Jobs</button>
    </div>
    <p class="status-line" id="status">Loading live jobs...</p>
    <section class="grid-system" id="jobs"></section>
  </main>
  <div class="noise"></div>
  <script src="/static/js/main.js"></script>
  <script>
    function loadJobs(){
      const status = document.getElementById('status');
      status.textContent = 'Searching live restaurant jobs...';
      fetch('/api/jobs')
        .then(r => r.json())
        .then(payload => {
          status.textContent = `Showing ${payload.count || 0} live restaurant jobs under 35 min transit and within 2.5 miles.`;
          window.UI && window.UI.renderJobs(payload.data || []);
        })
        .catch(err => {
          console.error(err);
          status.textContent = 'Live job search failed. Check /api/health and Cloud Run logs.';
        });
    }
    loadJobs();
  </script>
</body>
</html>
""")

@app.route("/api/health", methods=["GET"])
def health():
    origin_latlng = geocode(Config.ORIGIN_ADDRESS)

    return jsonify({
        "status": "ok",
        "service": "job-hunter-pro",
        "runtime": "google-cloud-run",
        "maps_enabled": bool(Config.GOOGLE_MAPS_API_KEY),
        "serpapi_enabled": bool(Config.SERPAPI_KEY),
        "groq_enabled": bool(Config.GROQ_API_KEY),
        "origin_address_configured": bool(Config.ORIGIN_ADDRESS),
        "origin_geocoded": bool(origin_latlng),
        "job_location": Config.JOB_LOCATION,
        "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
        "max_radius_miles": Config.MAX_RADIUS_MILES,
        "food_only": True,
    })

@app.route("/api/jobs", methods=["GET"])
def jobs():
    data = fetch_serpapi_jobs()

    return jsonify({
        "status": "success",
        "source": "serpapi_google_jobs_live",
        "count": len(data),
        "rules": {
            "food_only": True,
            "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
            "max_radius_miles": Config.MAX_RADIUS_MILES,
            "origin": Config.ORIGIN_ADDRESS,
            "job_location": Config.JOB_LOCATION,
        },
        "data": data,
    })

@app.route("/api/demo", methods=["GET"])
def demo_alias():
    return jobs()

@app.route("/api/search", methods=["POST"])
def search_jobs():
    payload = request.get_json(silent=True) or {}
    raw_jobs = payload.get("jobs")

    if isinstance(raw_jobs, list):
        processed = []

        for raw in raw_jobs:
            if not isinstance(raw, dict):
                continue

            job = {
                "title": clean_text(raw.get("title"), "Untitled Restaurant Role"),
                "company": clean_text(raw.get("company") or raw.get("employer"), "Company not listed"),
                "location": clean_text(raw.get("location"), Config.JOB_LOCATION),
                "salary": clean_text(raw.get("salary") or raw.get("pay"), "Salary not listed"),
                "description": clean_text(raw.get("description") or raw.get("summary"), "No description available."),
                "source_url": clean_text(raw.get("source_url") or raw.get("url")),
            }

            commute = get_commute(job["location"])
            job.update(commute)
            job["tags"] = infer_tags(job)
            job["match"] = calculate_match(job)

            if is_food_job(job) and passes_location_rules(job):
                processed.append(job)

        processed.sort(key=lambda job: (
            job["distance_miles"] if job["distance_miles"] is not None else 999,
            job["commute_seconds"] if job["commute_seconds"] is not None else 999999,
            -job["match"],
        ))

        return jsonify({
            "status": "success",
            "source": "posted_payload_filtered",
            "count": len(processed),
            "data": processed,
        })

    return jobs()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
