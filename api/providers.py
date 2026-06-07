from flask import jsonify
from api import api_bp
from providers import get_all_providers

@api_bp.route('/providers', methods=['GET'])
def providers():
    """Returns a list of all providers and their current status."""
    all_providers = get_all_providers()
    data = []
    for p in all_providers:
        meta = p.metadata
        data.append({
            "key": meta.key,
            "label": meta.label,
            "type": meta.type.value,
            "description": meta.description,
            "is_available": p.is_available(),
            "requires_api_key": meta.requires_api_key
        })
    return jsonify({"providers": data})
