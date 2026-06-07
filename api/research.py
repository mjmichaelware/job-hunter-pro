from flask import jsonify
from api import api_bp

@api_bp.route('/research', methods=['GET'])
def research():
    return jsonify({"message": "Research endpoint (placeholder)"})
