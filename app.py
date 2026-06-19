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

    # Capture incoming query string
    qs = request.query_string.decode('utf-8') if request.query_string else None

    with real_api_app.test_client() as client:
        result = client.open(
            path=target_path,
            method=request.method,
            query_string=qs,
            headers=dict(_copy_request_headers()),
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

    @app.get("/sw.js")
    def service_worker():
        # Served from root so the worker controls the whole "/" scope (PWA offline).
        resp = send_from_directory(STATIC_DIR, "sw.js", mimetype="application/javascript")
        resp.headers["Service-Worker-Allowed"] = "/"
        resp.headers["Cache-Control"] = "no-cache"
        return resp

    @app.get("/offline.html")
    def offline():
        return render_template("offline.html")

    @app.get("/api/_surface")
    def surface():
        return jsonify({
            "status": "ok",
            "entrypoint": "app:app",
            "ui": "web/templates/index.html",
            "static": "web/static",
            "api_backend": "api.index:app",
            "api_index_proxy_routes": "enabled",
            "modular_routes": "enabled (providers, industries, applications, ingest)",
            "placeholder_blueprint_registered": False,
            "truth": "S10 cockpit is served from web/. Traffic for core discovery/history is proxied to api.index. Modular routes handle metadata and local state.",
        })

    from api import api_bp
    app.register_blueprint(api_bp)

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
