from __future__ import annotations

import hashlib
import inspect
import logging
from typing import Any, Dict, Iterable, List, Tuple

logger = logging.getLogger(__name__)


def _metadata_value(provider: Any, name: str, default: Any = None) -> Any:
    metadata = getattr(provider, "metadata", None)
    return getattr(metadata, name, default)


def _provider_key(provider: Any) -> str:
    return str(_metadata_value(provider, "key", provider.__class__.__name__.lower()))


def _provider_label(provider: Any) -> str:
    return str(_metadata_value(provider, "label", _provider_key(provider)))


def _provider_available(provider: Any) -> bool:
    attr = getattr(provider, "is_available", None)
    if callable(attr):
        try:
            return bool(attr())
        except Exception:
            return False
    if attr is not None:
        return bool(attr)

    available = getattr(provider, "available", None)
    if callable(available):
        try:
            return bool(available())
        except Exception:
            return False
    if available is not None:
        return bool(available)

    return True


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    out: Dict[str, Any] = {}
    for name in dir(value):
        if name.startswith("_"):
            continue
        try:
            attr = getattr(value, name)
        except Exception:
            continue
        if callable(attr):
            continue
        if name in {"title", "url", "snippet", "provider", "query", "source", "source_name", "published_date", "raw_json", "raw", "confidence"}:
            out[name] = attr
    return out


def _pick(*sources: Dict[str, Any], keys: Iterable[str], default: str = "") -> str:
    for source in sources:
        for key in keys:
            value = source.get(key)
            if value not in (None, ""):
                return str(value)
    return default


def _call_provider_search(provider: Any, query: str, location: str, limit: int) -> List[Any]:
    method = getattr(provider, "search", None)
    if not callable(method):
        return []

    try:
        sig = inspect.signature(method)
        params = sig.parameters
        kwargs: Dict[str, Any] = {}

        for name in params:
            if name in {"self"}:
                continue
            if name in {"query", "q", "keywords", "what"}:
                kwargs[name] = query
            elif name in {"location", "where", "place"}:
                kwargs[name] = location
            elif name in {"limit", "max_results", "num_results", "results_per_page", "page_size"}:
                kwargs[name] = max(1, min(limit, 10))

        if kwargs:
            results = method(**kwargs)
        else:
            results = method(query)

    except TypeError:
        try:
            results = method(query, location)
        except TypeError:
            results = method(query)
    except Exception:
        raise

    if results is None:
        return []
    if isinstance(results, list):
        return results
    return list(results)


def _result_to_raw(item: Any, provider_key: str, provider_label: str, query: str, default_location: str) -> Dict[str, Any]:
    item_dict = _as_dict(item)
    raw_payload = item_dict.get("raw") or item_dict.get("raw_json") or item_dict.get("raw_payload") or {}
    raw_dict = _as_dict(raw_payload)

    title = _pick(item_dict, raw_dict, keys=["title", "job_title", "name"], default="Untitled job")
    company = _pick(
        item_dict,
        raw_dict,
        keys=["company", "company_name", "employer", "organization", "source_name", "source"],
        default=provider_label,
    )
    url = _pick(item_dict, raw_dict, keys=["url", "source_url", "apply_url", "redirect_url", "link"], default="")
    snippet = _pick(item_dict, raw_dict, keys=["snippet", "description", "summary", "body"], default="")
    location = _pick(item_dict, raw_dict, keys=["location", "formatted_location", "candidate_required_location", "where"], default=default_location)

    identity = hashlib.sha256(f"{provider_key}|{query}|{title}|{company}|{url}".encode("utf-8")).hexdigest()

    raw = dict(raw_dict)
    raw.update({
        "job_id": raw.get("job_id") or identity,
        "title": title,
        "company_name": company,
        "company": company,
        "location": location,
        "description": snippet,
        "snippet": snippet,
        "share_link": url,
        "url": url,
        "source_url": url,
        "via": provider_label,
        "source": provider_key,
        "_provider": provider_key,
        "_provider_label": provider_label,
        "_query_used": query,
        "_federated": True,
    })
    return raw


def fetch_provider_raw_jobs(queries: List[str], max_raw_jobs: int, location: str = "Salt Lake City, UT") -> Dict[str, Any]:
    from providers import get_providers_by_type
    from providers.base import ProviderType

    search_providers = list(get_providers_by_type(ProviderType.SEARCH))
    raw_jobs: List[Dict[str, Any]] = []
    seen = set()
    provider_breakdown: Dict[str, Dict[str, Any]] = {}

    for provider in search_providers:
        key = _provider_key(provider)
        label = _provider_label(provider)

        provider_breakdown[key] = {
            "label": label,
            "available": False,
            "queries_attempted": 0,
            "raw_count": 0,
            "status": "dormant",
        }

        if not _provider_available(provider):
            continue

        provider_breakdown[key]["available"] = True
        provider_breakdown[key]["status"] = "ok"

        for query in queries:
            if len(raw_jobs) >= max_raw_jobs:
                break

            provider_breakdown[key]["queries_attempted"] += 1

            try:
                results = _call_provider_search(provider, query, location, max_raw_jobs - len(raw_jobs))
            except Exception as exc:
                provider_breakdown[key]["status"] = "error"
                provider_breakdown[key]["error"] = f"{type(exc).__name__}: {str(exc)[:180]}"
                logger.warning("Provider %s failed for query %s", key, query, exc_info=True)
                continue

            for item in results:
                raw = _result_to_raw(item, key, label, query, location)
                identity = raw.get("job_id") or f"{raw.get('title')}|{raw.get('company_name')}|{raw.get('source_url')}"
                if identity in seen:
                    continue
                seen.add(identity)
                raw_jobs.append(raw)
                provider_breakdown[key]["raw_count"] += 1
                if len(raw_jobs) >= max_raw_jobs:
                    break

    return {
        "raw_jobs": raw_jobs,
        "query_count": len(queries),
        "provider_breakdown": provider_breakdown,
    }
