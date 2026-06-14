from flask import jsonify
from api import api_bp
from providers import get_all_providers

@api_bp.route('/providers', methods=['GET'])
def providers():
    """Returns a list of all providers and their current status."""
    try:
        from services.provider_status import is_policy_disabled, policy_disable_reason
    except Exception:
        is_policy_disabled = lambda k: False
        policy_disable_reason = lambda k: ""

    all_providers = get_all_providers()
    data = []
    for p in all_providers:
        meta = p.metadata
        disabled = is_policy_disabled(meta.key)
        if disabled:
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
            "disabled_by_policy": disabled,
            "status": status,
            "reason": policy_disable_reason(meta.key) if disabled else "",
            "requires_api_key": meta.requires_api_key
        })
    return jsonify({"providers": data})
