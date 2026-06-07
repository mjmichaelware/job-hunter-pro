"""
Disabled legacy scrape endpoint.

This file is intentionally inert. Do not place provider keys, database URLs,
passwords, or tokens here. Ingestion belongs behind the approved protected
scheduler/OIDC path only.
"""

from flask import jsonify

def trigger_scrape():
    return jsonify({
        "status": "disabled",
        "reason": "legacy_scrape_endpoint_disabled",
        "message": "Use the protected scheduler/OIDC ingestion path.",
    }), 410
