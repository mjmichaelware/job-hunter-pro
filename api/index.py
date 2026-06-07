import os
import re
import logging
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict, List, Optional

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
    BASE_LOCATION = os.environ.get("BASE_LOCATION", "84115").strip()
    MAX_COMMUTE_SECONDS = int(os.environ.get("MAX_COMMUTE_SECONDS", "2700"))
    REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "8"))

session = requests.Session()

def clean_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text if text else fallback

def infer_tags(job: Dict[str, Any]) -> List[str]:
    raw = " ".join([
        clean_text(job.get("title")),
        clean_text(job.get("description")),
        clean_text(job.get("company")),
        clean_text(job.get("location")),
    ]).lower()

    tags = []

    rules = [
        ("remote", ["remote", "work from home", "wfh"]),
        ("hybrid", ["hybrid"]),
        ("entry-level", ["entry level", "junior", "trainee"]),
        ("full-time", ["full time", "full-time"]),
        ("part-time", ["part time", "part-time"]),
        ("customer-service", ["customer service", "support", "call center"]),
        ("sales", ["sales", "account executive", "closer"]),
        ("warehouse", ["warehouse", "forklift", "inventory"]),
        ("food-service", ["cook", "prep", "restaurant", "kitchen"]),
        ("behavioral-health", ["case manager", "behavioral health", "peer support", "recovery"]),
    ]

    for tag, keywords in rules:
        if any(keyword in raw for keyword in keywords):
            tags.append(tag)

    existing = job.get("tags", [])
    if isinstance(existing, list):
        for tag in existing:
            safe = clean_text(tag)
            if safe and safe not in tags:
                tags.append(safe)

    return tags[:5]

@lru_cache(maxsize=256)
def get_commute_seconds(destination: str) -> Optional[int]:
    destination = clean_text(destination)
    if not destination:
        return None

    if not Config.GOOGLE_MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY missing. Commute unavailable.")
        return None

    try:
        response = session.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params={
                "origins": Config.BASE_LOCATION,
                "destinations": destination,
                "mode": "transit",
                "key": Config.GOOGLE_MAPS_API_KEY,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        element = data.get("rows", [{}])[0].get("elements", [{}])[0]
        if element.get("status") != "OK":
            logger.warning("Maps returned %s for %s", element.get("status"), destination)
            return None

        return int(element["duration"]["value"])

    except Exception as exc:
        logger.exception("Commute lookup failed for %s: %s", destination, exc)
        return None

def calculate_match(job: Dict[str, Any], commute_seconds: Optional[int]) -> int:
    score = 72
    text = " ".join([
        clean_text(job.get("title")),
        clean_text(job.get("description")),
        clean_text(job.get("company")),
    ]).lower()

    boosts = {
        "remote": 8,
        "hybrid": 5,
        "entry": 6,
        "support": 5,
        "customer": 5,
        "sales": 4,
        "case manager": 7,
        "peer support": 9,
        "behavioral health": 8,
        "cook": 3,
        "prep": 3,
    }

    for keyword, points in boosts.items():
        if keyword in text:
            score += points

    if commute_seconds is not None:
        if commute_seconds <= 900:
            score += 10
        elif commute_seconds <= 1800:
            score += 6
        elif commute_seconds <= 2700:
            score += 2
        else:
            score -= 10

    supplied = job.get("match")
    if supplied is not None:
        try:
            score = max(score, int(float(supplied)))
        except Exception:
            pass

    return max(1, min(score, 99))

def normalize_job(job: Dict[str, Any]) -> Dict[str, Any]:
    title = clean_text(job.get("title"), "Untitled Role")
    company = clean_text(job.get("company") or job.get("employer"), "Company not listed")
    location = clean_text(job.get("location"), "Location not listed")
    salary = clean_text(job.get("salary") or job.get("pay"), "Salary not listed")
    description = clean_text(job.get("description") or job.get("summary"), "No description available yet.")

    commute_seconds = get_commute_seconds(location)
    commute_label = "Commute unavailable"

    if commute_seconds is not None:
        commute_label = f"{round(commute_seconds / 60)}m commute"

    return {
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "description": description,
        "commute_seconds": commute_seconds,
        "commute_label": commute_label,
        "tags": infer_tags(job),
        "match": calculate_match(job, commute_seconds),
        "source_url": clean_text(job.get("source_url") or job.get("url")),
    }

def should_keep_job(job: Dict[str, Any]) -> bool:
    commute = job.get("commute_seconds")
    if commute is None:
        return True
    return int(commute) <= Config.MAX_COMMUTE_SECONDS

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
    <p class="lead">Backend is live. API routes are serving from Google Cloud Run.</p>
    <div class="cluster">
      <a class="btn btn-primary" href="/api/health">Health Check</a>
      <a class="btn btn-ghost" href="/api/demo">Demo Jobs</a>
    </div>
    <section class="grid-system" id="jobs"></section>
  </main>
  <div class="noise"></div>
  <script src="/static/js/main.js"></script>
  <script>
    fetch('/api/demo')
      .then(r => r.json())
      .then(payload => window.UI && window.UI.renderJobs(payload.data || []))
      .catch(err => console.error(err));
  </script>
</body>
</html>
""")

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "job-hunter-pro",
        "runtime": "google-cloud-run",
        "maps_enabled": bool(Config.GOOGLE_MAPS_API_KEY),
        "serpapi_enabled": bool(Config.SERPAPI_KEY),
        "groq_enabled": bool(Config.GROQ_API_KEY),
        "base_location": Config.BASE_LOCATION,
        "max_commute_seconds": Config.MAX_COMMUTE_SECONDS,
    })

@app.route("/api/search", methods=["POST"])
def search_jobs():
    payload = request.get_json(silent=True) or {}
    raw_jobs = payload.get("jobs", [])

    if not isinstance(raw_jobs, list):
        return jsonify({
            "status": "error",
            "error": "Expected JSON body with jobs as a list.",
            "example": {
                "jobs": [
                    {
                        "title": "Prep Cook",
                        "company": "Example",
                        "location": "Salt Lake City, UT"
                    }
                ]
            },
        }), 400

    processed = []

    for item in raw_jobs:
        if isinstance(item, dict):
            normalized = normalize_job(item)
            if should_keep_job(normalized):
                processed.append(normalized)

    processed.sort(key=lambda job: (
        job["commute_seconds"] is None,
        job["commute_seconds"] if job["commute_seconds"] is not None else 999999,
        -job["match"],
    ))

    return jsonify({
        "status": "success",
        "count": len(processed),
        "data": processed,
    })

@app.route("/api/demo", methods=["GET"])
def demo_jobs():
    raw_jobs = [
        {
            "title": "Peer Support Specialist",
            "company": "Community Recovery Center",
            "location": "Salt Lake City, UT",
            "salary": "$18-$24/hr",
            "description": "Entry-level peer support role helping clients with recovery resources, appointments, and stabilization.",
            "tags": ["behavioral-health", "entry-level"],
        },
        {
            "title": "Prep Cook",
            "company": "Downtown Restaurant Group",
            "location": "Salt Lake City, UT",
            "salary": "$17-$21/hr",
            "description": "Kitchen prep, line support, sanitation, and service readiness.",
            "tags": ["food-service"],
        },
        {
            "title": "Customer Support Representative",
            "company": "Local Services Team",
            "location": "Murray, UT",
            "salary": "$19/hr",
            "description": "Phone and chat support for customer scheduling, account questions, and issue resolution.",
            "tags": ["customer-service"],
        },
    ]

    processed = [normalize_job(job) for job in raw_jobs]
    processed = [job for job in processed if should_keep_job(job)]
    processed.sort(key=lambda job: (
        job["commute_seconds"] is None,
        job["commute_seconds"] if job["commute_seconds"] is not None else 999999,
        -job["match"],
    ))

    return jsonify({
        "status": "success",
        "count": len(processed),
        "data": processed,
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
