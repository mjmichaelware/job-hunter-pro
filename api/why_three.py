from flask import jsonify
from api import api_bp

@api_bp.route('/why-three', methods=['GET'])
def why_three():
    return jsonify({"message": "Why three endpoint (placeholder)"})
