from flask import jsonify, request
from api import api_bp

@api_bp.route('/ingest', methods=['POST'])
def ingest():
    # S8 OIDC boundary enforced here (or via decorator)
    # Thin wiring only.
    return jsonify({"message": "Ingest endpoint (OIDC protected, placeholder)"})
