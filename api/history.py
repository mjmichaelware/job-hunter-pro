from flask import jsonify
from api import api_bp

@api_bp.route('/history', methods=['GET'])
def history():
    return jsonify({"message": "History endpoint (placeholder)"})
