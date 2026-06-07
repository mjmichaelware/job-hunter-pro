from flask import jsonify
from api import api_bp

@api_bp.route('/usage', methods=['GET'])
def usage():
    return jsonify({"message": "Usage endpoint (placeholder)"})
