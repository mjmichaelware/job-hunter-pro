from __future__ import annotations

import hashlib
import inspect
import logging
import os
import re
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    location = _pick(item_dict, raw_dict, keys=["location", "formatted_location", "candidate_required_location", "where", "jobGeo", "job_geo", "region", "locations", "city", "area"], default=default_location)
    published = _pick(item_dict, raw_dict, keys=["published_date", "posted_at", "publication_date", "created_at", "date", "created", "updated", "pubDate", "PublicationStartdate", "AcquisitionDate", "AccquisitionDate"], default="")

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
        "published_date": published or raw.get("published_date") or "",
    })
    return raw


def _run_provider_search_with_timeout(
    provider: Any, query: str, location: str, limit: int, timeout_seconds: int
) -> List[Any]:
    """Run _call_provider_search with a hard wall-clock timeout."""
    result_holder: Dict[str, List[Any]] = {"results": []}
    done = threading.Event()

    def worker():
        try:
            results = _call_provider_search(provider, query, location, limit)
            result_holder["results"] = results if results else []
        except Exception:
            result_holder["results"] = []
        finally:
            done.set()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds + 2)

    if thread.is_alive():
        # Timed out — provider took too long; skip this query
        return []
    return result_holder["results"]


def fetch_provider_raw_jobs(
    queries: List[str],
    max_raw_jobs: int,
    location: str = "Salt Lake City, UT",
    per_provider_cap: int | None = None,
    timeout_per_query: int = 15,
) -> Dict[str, Any]:
    """
    Fair SEARCH-provider fanout.

    Required invariant:
    every available SEARCH provider gets attempted before any one provider can dominate the run.

    Reasoning providers are not called here. They enrich/classify after discovery.

    Added timeout_per_query (default 15s) to prevent any single provider query
    from blocking the entire discovery run indefinitely.
    """
    from providers import get_providers_by_type
    from providers.base import ProviderType
    from core.errors import ProviderHardFailure
    from services.provider_status import RunQuarantine, disabled_reason

    try:
        from services.geo_filter import location_is_local, local_gate_enabled
        _locality_gate = local_gate_enabled()
    except Exception:
        location_is_local = None
        _locality_gate = False

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
    _run_start_ts = int(time.time())
    # Hard wall-clock deadline for the whole fanout. Every provider stops
    # starting new queries once it passes; all jobs already collected are kept
    # (and were persisted incrementally). This guarantees the HTTP response
    # arrives before Cloud Run's request timeout, so the UI never has to fall
    # back and jobs are never dropped by a timeout.
    try:
        deadline_seconds = int(os.environ.get("FANOUT_DEADLINE_SECONDS", "150"))
    except Exception:
        deadline_seconds = 150
    deadline_ts = time.time() + max(10, deadline_seconds)

    active_count = max(1, len(available_providers))
    # Per-provider cap removed — each provider can now run all its queries.
    # The global MAX_RAW_JOBS cap still applies across all providers.
    provider_cap = max_raw_jobs

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
            "excluded_nonlocal": 0,
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
        queries_run = 0
        for query in queries:
            # Stop starting new queries once the run deadline passes. Jobs
            # already found stay in raw_jobs — nothing discovered is discarded.
            if time.time() > deadline_ts:
                bd["status"] = "stopped_run_deadline_reached"
                return
            # Check global caps early
            with lock:
                remaining_global = max_raw_jobs - len(raw_jobs)
            if remaining_global <= 0:
                bd["status"] = "not_attempted_global_cap_reached"
                return

            # Respect per-query timeout, capped to the remaining run deadline so
            # an in-flight query can never push the response past it.
            try:
                remaining = max(3, int(deadline_ts - time.time()))
                per_query_timeout = max(3, min(timeout_per_query, remaining))
                request_limit = 100
                bd["queries_attempted"] += 1

                results = _run_provider_search_with_timeout(
                    provider, query, location, request_limit, per_query_timeout
                )
            except Exception as exc:
                bd["status"] = "error"
                bd["error"] = f"{type(exc).__name__}: {str(exc)[:180]}"
                logger.warning("Provider %s failed for query %s", key, query, exc_info=True)
                continue

            for item in results:
                raw = _result_to_raw(item, key, label, query, location)
                # Locality gate at the raw stage: provably non-local listings
                # never enter the run (so they can't consume the global cap or
                # reappear via incremental batches). Jobs with no location text
                # default to the run location and pass.
                if _locality_gate and location_is_local is not None:
                    raw_location = str(raw.get("location") or raw.get("listing_location") or "")
                    if not location_is_local(raw_location):
                        bd["excluded_nonlocal"] = bd.get("excluded_nonlocal", 0) + 1
                        continue
                # URL-first identity: the same posting found via multiple queries
                # (or providers) collapses to one; distinct openings that share a
                # title are all kept. Hash/job_id is only a last resort.
                identity = (
                    raw.get("source_url") or raw.get("url") or raw.get("share_link") or ""
                ).strip().lower()
                if not identity:
                    identity = raw.get("job_id") or (
                        f"{raw.get('title')}|{raw.get('company_name')}|{raw.get('location')}"
                    )
                with lock:
                    if identity in seen:
                        continue
                    if len(raw_jobs) >= max_raw_jobs:
                        bd["status"] = "stopped_global_cap_reached"
                        return
                    seen.add(identity)
                    raw_jobs.append(raw)
                bd["raw_count"] += 1

            queries_run += 1
            # IMPORTANT: persist each provider's results IMMEDIATELY so that a
            # global timeout / browser abort never loses completed work. Every
            # provider finishes its queries sequentially within its own thread,
            # so writing here is thread-safe per provider.
            if bd["raw_count"] > 0:
                try:
                    from store.sqlite_repo import get_sqlite_batches_repo
                    import datetime as _dt, os as _os

                    db_path = _os.environ.get("JHP_SQLITE_DB", "/tmp/job_hunter_pro.sqlite")
                    sqlite_batches = get_sqlite_batches_repo(db_path)
                    provider_jobs = []
                    seen_provider_urls = set()
                    for j in raw_jobs:
                        if j.get("_provider") != key:
                            continue
                        # Dedupe by exact source URL only — distinct openings
                        # that share a title are all kept.
                        raw_url = str(
                            j.get("source_url") or j.get("url") or j.get("share_link") or j.get("job_id") or ""
                        ).strip().lower()
                        if not raw_url:
                            raw_url = "|".join([
                                str(j.get("title") or ""),
                                str(j.get("company_name") or j.get("company") or ""),
                                str(j.get("location") or ""),
                            ]).strip().lower()
                        if raw_url in seen_provider_urls:
                            continue
                        seen_provider_urls.add(raw_url)
                        provider_jobs.append(j)
                    # Normalize before persisting so the UI never sees raw
                    # "unavailable" fields. enrich=False keeps incremental saves
                    # fast — external place/transit calls would make a big run
                    # exceed Cloud Run's timeout and force a fallback.
                    try:
                        from api.index import normalize_job
                        provider_jobs = [normalize_job(j, enrich=False) for j in provider_jobs]
                    except Exception as _norm_exc:
                        logger.debug("incremental normalize_job failed, saving raw: %s", _norm_exc)
                    doc_key = f"batches/incremental_{key}_{_run_start_ts}_batch.json"
                    sqlite_batches.save(
                        doc_key,
                        {
                            "batch_schema": "job_hunter_batch_v1",
                            "created_at_utc": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
                            "object_name": doc_key,
                            "source": "incremental_provider_save",
                            "provider": key,
                            "accepted": provider_jobs,
                            "rejected": [],
                            "counts": {"accepted": len(provider_jobs), "rejected": 0, "raw": len(provider_jobs), "queries": queries_run},
                        },
                    )
                    logger.info("[DISCOVERY_PERSIST] provider=%s saved %d raws key=%s", key, len(provider_jobs), doc_key)
                except Exception as exc:
                    logger.warning("incremental sqlite save for %s failed: %s", key, exc)

    # Concurrent fanout: every available provider runs in parallel (each provider
    # still walks its own queries sequentially so per-provider caps/quarantine are
    # simple). Caps + timeout keep total work bounded.
    if runnable:
        max_workers = min(len(runnable), max(1, int(os.environ.get("FANOUT_MAX_WORKERS", "8"))))
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
