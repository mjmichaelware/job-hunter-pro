from flask import jsonify
from api import api_bp
from providers import get_all_providers

@api_bp.route('/providers', methods=['GET'])
def providers():
    """Returns a list of all providers and their current status."""
    try:
        from services.provider_status import disabled_reason
    except Exception:
        disabled_reason = lambda p: ""

    all_providers = get_all_providers()
    data = []
    for p in all_providers:
        meta = p.metadata
        reason = disabled_reason(p)
        if reason:
            status = "disabled_by_policy"
        elif p.is_available():
            status = "ready"
        else:
            status = "dormant"
        data.append({
            "key": meta.key,
            "label": meta.label,
            "type": meta.type.value,
            "description": meta.description,
            "is_available": p.is_available(),
            "disabled_by_policy": bool(reason),
            "status": status,
            "reason": reason,
            "requires_api_key": meta.requires_api_key
        })
    return jsonify({"providers": data})
