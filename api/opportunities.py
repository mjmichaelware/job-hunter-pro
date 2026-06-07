from flask import jsonify
from api import api_bp

@api_bp.route('/opportunities', methods=['GET'])
def opportunities():
    return jsonify({"message": "Opportunities endpoint (placeholder)"})
