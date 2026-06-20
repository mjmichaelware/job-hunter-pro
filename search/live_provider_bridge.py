from __future__ import annotations

import hashlib
import inspect
import logging
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

logger = logging.getLogger(__name__)

_LOC_NOISE = re.compile(r'\b(jobs?|near|hiring|positions?|openings?|salt lake city|slc|utah|ut|\d{5})\b', re.I)

# ---------------------------------------------------------------------------
# Cross-provider canonical dedup helpers
#
# Problem this solves: the old per-result identity included provider_key and
# the raw URL, so the same role posted by two different providers (or posted
# with a tracking-param-different URL) produced two separate seen-set entries
# and both leaked into raw_jobs as apparent duplicates.
#
# Solution: build a canonical key from normalized (title, company, location)
# that is INDEPENDENT of provider and URL.  Two results that normalize to the
# same (title, company, location) tuple collapse to one entry in the seen-set
# regardless of source.  Only when both company AND location are empty (to
# avoid collapsing two genuinely different untitled/unlocated jobs) do we fall
# back to including the stripped URL so we do not over-collapse.
# ---------------------------------------------------------------------------

_PUNC_RE = re.compile(r'[^\w\s]')
_SPACE_RE = re.compile(r'\s+')
_CORP_NOISE = re.compile(
    r'\b(inc|llc|ltd|corp|co|company|group|solutions|services|staffing|partners|associates)\b',
    re.I,
)
# URL query params that are purely tracking/session noise and should be stripped
# before comparing URLs across providers.
_TRACKING_PARAMS = frozenset({
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
    'ref', 'referer', 'referrer', 'source', 'src', 'cid', 'gclid', 'fbclid',
    'msclkid', 'via', 'tracking_id', 'affiliate', 'campaign',
})


def _normalize_field(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, remove corp noise."""
    t = (text or "").lower()
    t = _PUNC_RE.sub(' ', t)
    t = _CORP_NOISE.sub(' ', t)
    t = _SPACE_RE.sub(' ', t).strip()
    return t


def _strip_tracking_params(url: str) -> str:
    """Remove known tracking query parameters from a URL for comparison."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=False)
        clean_qs = {k: v for k, v in qs.items() if k.lower() not in _TRACKING_PARAMS}
        new_query = urlencode(sorted(clean_qs.items()), doseq=True)
        return urlunparse(parsed._replace(query=new_query))
    except Exception:
        return url


def _canonical_dedup_key(title: str, company: str, location: str, url: str = "") -> str:
    """
    Cross-provider dedup key: independent of provider identity and raw URL.

    When company AND location are both empty we cannot reliably distinguish two
    different jobs, so we append the stripped URL to avoid over-collapsing.
    In all other cases the key is purely (norm_title, norm_company, norm_location).
    """
    nt = _normalize_field(title)
    nc = _normalize_field(company)
    nl = _normalize_field(location)

    if not nc and not nl:
        # Both anchor fields empty — use URL as tiebreaker to stay conservative.
        fallback = _strip_tracking_params(url)
        return hashlib.sha256(f"{nt}|{fallback}".encode()).hexdigest()

    return hashlib.sha256(f"{nt}|{nc}|{nl}".encode()).hexdigest()


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

    # Provider-scoped identity (used as job_id for stable reference within a run).
    # This is NOT used for the cross-provider seen-set — see _canonical_dedup_key.
    provider_identity = hashlib.sha256(
        f"{provider_key}|{query}|{title}|{company}|{url}".encode("utf-8")
    ).hexdigest()

    # Cross-provider canonical key for the shared dedup seen-set.
    # Independent of provider_key and raw URL so the same role from two providers
    # collapses to one entry.  Stored on the raw dict so callers can inspect it.
    cross_key = _canonical_dedup_key(title, company, location, url)

    raw = dict(raw_dict)
    raw.update({
        "job_id": raw.get("job_id") or provider_identity,
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
        "_canonical_key": cross_key,  # cross-provider dedup key, visible in debug output
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
    # One lock guards the shared raw_jobs list, the seen-dedupe set, and the
    # quarantine ledger. Each provider's own breakdown entry is written only by
    # that provider's worker thread, so it needs no lock.
    lock = threading.Lock()

    active_count = max(1, len(available_providers))
    fair_default_cap = max(1, (max_raw_jobs + active_count - 1) // active_count)
    provider_cap = int(per_provider_cap or fair_default_cap)

    # First pass (single thread): seed a breakdown entry for EVERY provider and
    # collect the ones that should actually run. Keeps dormant/disabled providers
    # visible in the response exactly as before.
    runnable: List[Any] = []
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
        runnable.append((provider, key, label))

    def _run_provider(provider: Any, key: str, label: str) -> None:
        bd = provider_breakdown[key]
        for query in queries:
            if bd["raw_count"] >= provider_cap:
                bd["status"] = "stopped_provider_cap_reached"
                return
            with lock:
                remaining_global = max_raw_jobs - len(raw_jobs)
            if remaining_global <= 0:
                bd["status"] = "not_attempted_global_cap_reached"
                return

            remaining_provider = provider_cap - bd["raw_count"]
            request_limit = max(1, min(remaining_global, remaining_provider, 100))
            bd["queries_attempted"] += 1

            try:
                results = _call_provider_search(provider, query, location, request_limit)
            except ProviderHardFailure as hard:
                # Hard auth/rate-limit failure (401/403/429): quarantine this
                # provider for the rest of the run so we do not hammer a dead
                # source across the whole keyword fanout.
                reason = f"quarantined_http_{hard.status_code}"
                with lock:
                    quarantine.quarantine(key, reason)
                bd["status"] = reason
                bd["quarantined"] = True
                bd["error"] = f"HTTP {hard.status_code} hard failure; stopped retrying this run."
                logger.warning("Provider %s quarantined for run after HTTP %s", key, hard.status_code)
                return
            except Exception as exc:
                bd["status"] = "error"
                bd["error"] = f"{type(exc).__name__}: {str(exc)[:180]}"
                logger.warning("Provider %s failed for query %s", key, query, exc_info=True)
                continue

            for item in results:
                raw = _result_to_raw(item, key, label, query, location)
                # Use the cross-provider canonical key for dedup so the same role
                # from two providers (or with tracking-param-different URLs) is
                # treated as one listing.  Falls back to a title+company+url string
                # only if the canonical key is somehow absent (should not happen).
                cross_key = raw.get("_canonical_key") or (
                    f"{raw.get('title')}|{raw.get('company_name')}|{raw.get('source_url')}"
                )
                with lock:
                    if cross_key in seen:
                        continue
                    if len(raw_jobs) >= max_raw_jobs:
                        return
                    seen.add(cross_key)
                    raw_jobs.append(raw)
                bd["raw_count"] += 1

                if bd["raw_count"] >= provider_cap:
                    bd["status"] = "stopped_provider_cap_reached"
                    return

        if bd["available"] and bd["raw_count"] == 0 and bd["status"] == "ok":
            bd["status"] = "available_returned_zero"

    # Concurrent fanout: every available provider runs in parallel (each provider
    # still walks its own queries sequentially so per-provider caps/quarantine are
    # simple). This is what lets the run scale to many providers without the old
    # sequential timeout. Caps + MAX_QUERIES keep total work bounded.
    if runnable:
        max_workers = min(len(runnable), max(1, int(os.environ.get("FANOUT_MAX_WORKERS", "12"))))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_provider, p, k, l) for (p, k, l) in runnable]
            for future in futures:
                # Each worker handles its own exceptions; surface anything unexpected.
                future.result()

    return {
        "raw_jobs": raw_jobs[:max_raw_jobs],
        "query_count": len(queries),
        "provider_breakdown": provider_breakdown,
        "provider_cap": provider_cap,
        "max_raw_jobs": max_raw_jobs,
        "fair_fanout": True,
        "quarantined_providers": quarantine.as_dict(),
    }
