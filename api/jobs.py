from flask import jsonify
from api import api_bp

@api_bp.route('/jobs', methods=['GET'])
def jobs():
    return jsonify({"message": "Jobs endpoint (placeholder)"})
