from flask import jsonify
from api import api_bp

@api_bp.route('/providers', methods=['GET'])
def providers():
    return jsonify({"message": "Providers endpoint (placeholder)"})
