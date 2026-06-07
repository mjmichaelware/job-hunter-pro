from flask import jsonify
from api import api_bp
from industries import get_all_routes

@api_bp.route('/industries', methods=['GET'])
def industries():
    """Returns metadata for all registered industry routes."""
    routes = get_all_routes()
    data = []
    for r in routes:
        data.append({
            "key": r.key,
            "label": r.label,
            "positive_terms": list(r.positive_terms),
            "negative_terms": list(r.negative_terms),
            "queries": r.queries
        })
    return jsonify({"industries": data})
