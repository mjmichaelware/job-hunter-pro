from flask import jsonify
from api import api_bp

@api_bp.route('/industries', methods=['GET'])
def industries():
    return jsonify({"message": "Industries endpoint (placeholder)"})
