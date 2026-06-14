from __future__ import annotations

import hashlib
import inspect
import logging
import re
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)

_LOC_NOISE = re.compile(r'\b(jobs?|near|hiring|positions?|openings?|salt lake city|slc|utah|ut|\d{5})\b', re.I)


def _clean_keywords(query: str) -> str:
    q = (query or "").replace('"', ' ')
    q = _LOC_NOISE.sub(' ', q)
    q = re.sub(r'\s+', ' ', q).strip()
    return q or "jobs"


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
    return bool(attr) if attr is not None else True


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
        if not callable(attr):
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

    key = _provider_key(provider)
    if not str(key).startswith("serpapi"):
        query = _clean_keywords(query)

    try:
        sig = inspect.signature(method)
        kwargs: Dict[str, Any] = {}

        for name in sig.parameters:
            if name == "self":
                continue
            if name in {"query", "q", "keywords", "what"}:
                kwargs[name] = query
            elif name in {"location", "where", "place"}:
                kwargs[name] = location
            elif name in {"limit", "max_results", "num_results", "results_per_page", "page_size"}:
                kwargs[name] = max(1, min(limit, 100))

        result = method(**kwargs) if kwargs else method(query)
    except TypeError:
        try:
            result = method(query, location)
        except TypeError:
            result = method(query)
    except Exception:
        raise

    if result is None:
        return []
    if isinstance(result, list):
        return result
    return list(result)


def _result_to_raw(item: Any, provider_key: str, provider_label: str, query: str, default_location: str) -> Dict[str, Any]:
    item_dict = _as_dict(item)
    raw_payload = item_dict.get("raw") or item_dict.get("raw_json") or item_dict.get("raw_payload") or {}
    raw_dict = _as_dict(raw_payload)

    title = _pick(item_dict, raw_dict, keys=["title", "job_title", "name"], default="Untitled job")
    company = _pick(item_dict, raw_dict, keys=["company", "company_name", "employer", "organization", "source_name", "source"], default=provider_label)
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


def fetch_provider_raw_jobs(
    queries: List[str],
    max_raw_jobs: int,
    location: str = "Salt Lake City, UT",
    per_provider_cap: int | None = None,
) -> Dict[str, Any]:
    """
    Fair SEARCH-provider fanout.

    Required invariant:
    every available SEARCH provider gets attempted before any one provider can dominate the run.

    Reasoning providers are not called here. They enrich/classify after discovery.
    """
    from providers import get_providers_by_type
    from providers.base import ProviderType
    from core.errors import ProviderHardFailure
    from services.provider_status import RunQuarantine, disabled_reason

    search_providers = list(get_providers_by_type(ProviderType.SEARCH))
    available_providers = [
        p for p in search_providers
        if _provider_available(p) and not disabled_reason(p)
    ]

    quarantine = RunQuarantine()
    raw_jobs: List[Dict[str, Any]] = []
    seen = set()
    provider_breakdown: Dict[str, Dict[str, Any]] = {}

    active_count = max(1, len(available_providers))
    fair_default_cap = max(1, (max_raw_jobs + active_count - 1) // active_count)
    provider_cap = int(per_provider_cap or fair_default_cap)

    for provider in search_providers:
        key = _provider_key(provider)
        label = _provider_label(provider)
        is_available = _provider_available(provider)
        off_reason = disabled_reason(provider)

        if off_reason:
            status = "disabled_by_policy"
        elif is_available:
            status = "ok"
        else:
            status = "dormant"

        provider_breakdown[key] = {
            "label": label,
            "available": is_available and not off_reason,
            "disabled_by_policy": bool(off_reason),
            "queries_attempted": 0,
            "raw_count": 0,
            "status": status,
            "cap": provider_cap,
        }

        if off_reason:
            provider_breakdown[key]["reason"] = off_reason
            continue

        if not is_available:
            continue

        for query in queries:
            if provider_breakdown[key]["raw_count"] >= provider_cap:
                provider_breakdown[key]["status"] = "stopped_provider_cap_reached"
                break

            remaining_global = max_raw_jobs - len(raw_jobs)
            if remaining_global <= 0:
                provider_breakdown[key]["status"] = "not_attempted_global_cap_reached"
                break

            remaining_provider = provider_cap - provider_breakdown[key]["raw_count"]
            request_limit = max(1, min(remaining_global, remaining_provider, 100))

            provider_breakdown[key]["queries_attempted"] += 1

            try:
                results = _call_provider_search(provider, query, location, request_limit)
            except ProviderHardFailure as hard:
                # Hard auth/rate-limit failure (401/403/429): quarantine this
                # provider for the rest of the run so we do not hammer a dead
                # source across the whole keyword fanout.
                reason = f"quarantined_http_{hard.status_code}"
                quarantine.quarantine(key, reason)
                provider_breakdown[key]["status"] = reason
                provider_breakdown[key]["quarantined"] = True
                provider_breakdown[key]["error"] = f"HTTP {hard.status_code} hard failure; stopped retrying this run."
                logger.warning("Provider %s quarantined for run after HTTP %s", key, hard.status_code)
                break
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

                if provider_breakdown[key]["raw_count"] >= provider_cap:
                    provider_breakdown[key]["status"] = "stopped_provider_cap_reached"
                    break
                if len(raw_jobs) >= max_raw_jobs:
                    break

        if provider_breakdown[key]["available"] and provider_breakdown[key]["raw_count"] == 0 and provider_breakdown[key]["status"] == "ok":
            provider_breakdown[key]["status"] = "available_returned_zero"

    return {
        "raw_jobs": raw_jobs[:max_raw_jobs],
        "query_count": len(queries),
        "provider_breakdown": provider_breakdown,
        "provider_cap": provider_cap,
        "max_raw_jobs": max_raw_jobs,
        "fair_fanout": True,
        "quarantined_providers": quarantine.as_dict(),
    }
