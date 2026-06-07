from flask import jsonify
from api import api_bp
from search.usage_tracker import UsageTracker

# Note: In a real app, this might be a singleton or from a repo
usage_tracker = UsageTracker()

@api_bp.route('/usage', methods=['GET'])
def usage():
    """Returns current API usage and budget status."""
    return jsonify({
        "monthly_usage": usage_tracker.get_total_usage("all"),
        "total_searches_left": 200, # Placeholder for real quota
        "provider_usage": usage_tracker.usage_data,
        "status": "safe"
    })
