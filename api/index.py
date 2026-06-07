import os
import re
import logging
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict, List, Optional

import requests
from flask import Flask, jsonify, request, render_template

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
        ("case-management", ["case manager", "behavioral health", "peer support"]),
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

@lru_cache(maxsize=256)
def get_commute_seconds(destination: str) -> Optional[int]:
    destination = clean_text(destination)
    if not destination:
        return None

    if not Config.GOOGLE_MAPS_API_KEY:
        logger.info("GOOGLE_MAPS_API_KEY missing; commute unavailable.")
        return None

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": Config.BASE_LOCATION,
        "destinations": destination,
        "mode": "transit",
        "key": Config.GOOGLE_MAPS_API_KEY,
    }

    try:
        res = session.get(url, params=params, timeout=Config.REQUEST_TIMEOUT)
        res.raise_for_status()
        data = res.json()

        element = data.get("rows", [{}])[0].get("elements", [{}])[0]
        if element.get("status") != "OK":
            logger.warning("Maps returned non-OK element for %s: %s", destination, element.get("status"))
            return None

        return int(element["duration"]["value"])

    except Exception as exc:
        logger.exception("Commute calculation failed for %s: %s", destination, exc)
        return None

def normalize_job(job: Dict[str, Any]) -> Dict[str, Any]:
    title = clean_text(job.get("title"), "Untitled Role")
    company = clean_text(job.get("company") or job.get("employer"), "Company not listed")
    location = clean_text(job.get("location"), "Location not listed")
    salary = clean_text(job.get("salary") or job.get("pay"), "Salary not listed")
    description = clean_text(job.get("description") or job.get("summary"), "No description available yet.")

    commute_seconds = get_commute_seconds(location)
    commute_label = "Commute unavailable"

    if commute_seconds is not None:
        minutes = round(commute_seconds / 60)
        commute_label = f"{minutes}m commute"

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
    return render_template("index.html")

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "job-hunter-pro",
        "maps_enabled": bool(Config.GOOGLE_MAPS_API_KEY),
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
            "example": {"jobs": [{"title": "Prep Cook", "company": "Example", "location": "Salt Lake City, UT"}]},
        }), 400

    processed = []

    for item in raw_jobs:
        if not isinstance(item, dict):
            continue

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
    demo = [
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

    processed = [normalize_job(job) for job in demo]
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
