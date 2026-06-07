from pathlib import Path

from flask import Flask, jsonify, render_template, send_from_directory

from api import api_bp


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
TEMPLATE_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"


def create_app():
    app = Flask(
        __name__,
        template_folder=str(TEMPLATE_DIR),
        static_folder=str(STATIC_DIR),
        static_url_path="/static",
    )

    app.register_blueprint(api_bp)

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
            "scheduler": "not_created",
            "ingest_called": False,
        })

    return app


app = create_app()
