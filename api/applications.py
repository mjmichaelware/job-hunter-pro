from flask import jsonify
from api import api_bp

@api_bp.route('/applications', methods=['GET'])
def applications():
    return jsonify({"message": "Applications endpoint (placeholder)"})
