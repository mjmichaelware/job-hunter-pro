from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from werkzeug.datastructures import Headers

from api.index import app as real_api_app
import api.index as real_api


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
TEMPLATE_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

ALL_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
}


def _configured(value) -> bool:
    return bool(str(value or "").strip())


def _copy_request_headers():
    for key, value in request.headers.items():
        lower = key.lower()
        if lower in HOP_BY_HOP_HEADERS or lower == "host":
            continue
        yield key, value


def _copy_response_headers(source_headers) -> Headers:
    headers = Headers()
    for key, value in source_headers.items():
        if key.lower() in HOP_BY_HOP_HEADERS:
            continue
        headers.add(key, value)
    return headers


def _proxy_to_real_api(path: str):
    target_path = "/api/" + path.lstrip("/")

    if target_path == "/api/research":
        target_path = "/api/research/place"

    if target_path == "/api/search/federated":
        target_path = "/api/search"

    with real_api_app.test_client() as client:
        result = client.open(
            path=target_path,
            method=request.method,
            query_string=request.query_string,
            headers=list(_copy_request_headers()),
            data=request.get_data(),
            content_type=request.content_type,
            follow_redirects=False,
        )

    body = result.get_data()

    if b"endpoint (placeholder)" in body[:800].lower():
        return jsonify({
            "status": "error",
            "error": "placeholder_route_leak",
            "path": target_path,
            "message": "Request reached placeholder code instead of api.index real backend.",
        }), 502

    return Response(
        body,
        status=result.status_code,
        headers=_copy_response_headers(result.headers),
    )


def create_app():
    app = Flask(
        __name__,
        template_folder=str(TEMPLATE_DIR),
        static_folder=str(STATIC_DIR),
        static_url_path="/static",
    )

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/favicon.ico")
    def favicon():
        icon_svg = STATIC_DIR / "icon.svg"
        if icon_svg.exists():
            return send_from_directory(STATIC_DIR, "icon.svg", mimetype="image/svg+xml")
        return ("", 204)

    @app.get("/api/_surface")
    def surface():
        return jsonify({
            "status": "ok",
            "entrypoint": "app:app",
            "ui": "web/templates/index.html",
            "static": "web/static",
            "api_backend": "api.index:app",
            "placeholder_blueprint_registered": False,
            "truth": "S10 cockpit is served from web/. Real API traffic is dispatched to api.index.",
        })

    @app.get("/api/providers")
    @app.get("/api/providers/status")
    @app.get("/api/search/providers/status")
    def providers():
        cfg = real_api.Config
        serpapi_status = real_api.serpapi_account_status()

        providers = [
            {
                "name": "SerpAPI Jobs",
                "type": "discovery",
                "configured": _configured(cfg.SERPAPI_KEY),
                "status": "configured" if _configured(cfg.SERPAPI_KEY) else "missing_key",
                "live_capable": bool(_configured(cfg.SERPAPI_KEY) and real_api.serpapi_budget_allows_search()),
                "notes": "Google Jobs retrieval. /api/jobs without dry_run may spend SerpAPI quota.",
            },
            {
                "name": "Google Maps / Places",
                "type": "geo_places",
                "configured": _configured(cfg.GOOGLE_MAPS_API_KEY),
                "status": "configured" if _configured(cfg.GOOGLE_MAPS_API_KEY) else "missing_key",
                "live_capable": _configured(cfg.GOOGLE_MAPS_API_KEY),
                "notes": "Geocoding, Places Text Search, Nearby Search, Place Details, Distance Matrix.",
            },
            {
                "name": "Groq",
                "type": "reasoning",
                "configured": _configured(cfg.GROQ_API_KEY),
                "status": "configured" if _configured(cfg.GROQ_API_KEY) else "missing_key",
                "live_capable": False,
                "notes": "Key present; api.index does not use this as a job discovery provider.",
            },
            {
                "name": "OpenAI",
                "type": "reasoning",
                "configured": _configured(cfg.OPENAI_API_KEY),
                "status": "configured" if _configured(cfg.OPENAI_API_KEY) else "missing_key",
                "live_capable": False,
                "notes": "Key present; api.index does not use this as a job discovery provider.",
            },
            {
                "name": "Gemini",
                "type": "reasoning",
                "configured": _configured(cfg.GEMINI_API_KEY),
                "status": "configured" if _configured(cfg.GEMINI_API_KEY) else "missing_key",
                "live_capable": False,
                "notes": "Key present; api.index does not use this as a job discovery provider.",
            },
            {
                "name": "Claude",
                "type": "reasoning",
                "configured": _configured(cfg.ANTHROPIC_API_KEY),
                "status": "configured" if _configured(cfg.ANTHROPIC_API_KEY) else "missing_key",
                "live_capable": False,
                "notes": "Key present; api.index does not use this as a job discovery provider.",
            },
            {
                "name": "xAI / Grok",
                "type": "reasoning",
                "configured": _configured(cfg.XAI_API_KEY),
                "status": "configured" if _configured(cfg.XAI_API_KEY) else "missing_key",
                "live_capable": False,
                "notes": "Key present; api.index does not use this as a job discovery provider.",
            },
        ]

        return jsonify({
            "status": "ok",
            "source": "api.index.Config + api.index.serpapi_account_status",
            "providers": providers,
            "serpapi": serpapi_status,
            "budget": {
                "serpapi_budget_mode": cfg.SERPAPI_BUDGET_MODE,
                "serpapi_min_searches_left": cfg.SERPAPI_MIN_SEARCHES_LEFT,
                "max_serp_queries": cfg.MAX_SERP_QUERIES,
                "max_raw_jobs": cfg.MAX_RAW_JOBS,
                "max_ai_calls": cfg.MAX_AI_CALLS,
            },
            "truth": "LLM keys are reasoning/enrichment only unless a real web-search/grounding provider is implemented.",
        })

    @app.get("/api/industries")
    def industries():
        return jsonify({
            "status": "ok",
            "source": "compatibility boundary over current api.index backend",
            "active_backend_scope": "food_service_only",
            "industries": [
                {
                    "key": "food_service",
                    "label": "Food Service",
                    "enabled": True,
                    "status": "active_in_api_index",
                    "source": "api.index FOOD_TERMS / ROLE_QUERIES / ROLE_GROUPS",
                    "role_families": ["front-of-house", "back-of-house", "management", "food-service"],
                },
                {"key": "hospitality", "label": "Hospitality", "enabled": False, "status": "planned_not_wired_in_api_index"},
                {"key": "care_social", "label": "Care & Social Services", "enabled": False, "status": "planned_not_wired_in_api_index"},
                {"key": "sales", "label": "Sales", "enabled": False, "status": "planned_not_wired_in_api_index"},
                {"key": "customer_service", "label": "Customer Service", "enabled": False, "status": "planned_not_wired_in_api_index"},
                {"key": "retail_ops", "label": "Retail Operations", "enabled": False, "status": "planned_not_wired_in_api_index"},
            ],
        })

    @app.get("/api/applications")
    def applications():
        return jsonify({
            "status": "ok",
            "configured": False,
            "applications": [],
            "message": "Application tracker storage is not implemented in current api.index. Returning honest empty state.",
        })

    @app.route("/api/ingest", methods=["POST"])
    def ingest():
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({
                "status": "error",
                "error": "oidc_required",
                "message": "/api/ingest requires Authorization: Bearer OIDC. URL tokens are not accepted.",
            }), 401
        return _proxy_to_real_api("ingest")

    @app.route("/api/<path:path>", methods=ALL_METHODS)
    def api_dispatch(path):
        return _proxy_to_real_api(path)

    return app


app = create_app()
