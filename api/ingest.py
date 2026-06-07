from flask import jsonify, request
from api import api_bp
from ingest.oidc import verify_token, OIDCError
from core import Config
import os

@api_bp.route('/ingest', methods=['POST'])
def ingest():
    """
    Protected ingest endpoint.
    Requires OIDC Bearer token from Google Cloud Scheduler.
    """
    auth_header = request.headers.get("Authorization")
    
    # In production, these should be configured in core/config.py or env
    expected_audience = os.getenv("OIDC_EXPECTED_AUDIENCE")
    expected_email = os.getenv("OIDC_EXPECTED_EMAIL")

    try:
        claims = verify_token(
            auth_header,
            expected_audience=expected_audience,
            expected_email=expected_email
        )
        # If we reach here, token is valid
        # TODO: Trigger real ingestion logic (S8/S11)
        return jsonify({
            "status": "success",
            "message": "Ingest triggered",
            "identity": claims.email
        })
    except OIDCError as e:
        return jsonify({
            "status": "error",
            "error": "unauthorized",
            "message": str(e)
        }), 401
