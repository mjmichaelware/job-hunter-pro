#!/usr/bin/env bash
set -euo pipefail

echo "=== FAIR PROVIDER FANOUT FIX — LOCAL ONLY ==="
echo "NO DEPLOY. NO PUSH. NO LIVE /api/jobs. NO /api/ingest."
echo "PWD=$(pwd)"
echo

[ -f app.py ] || { echo "FAIL: not in repo root"; exit 1; }
[ -f api/index.py ] || { echo "FAIL: api/index.py missing"; exit 1; }
[ -f search/live_provider_bridge.py ] || { echo "FAIL: search/live_provider_bridge.py missing"; exit 1; }

echo "=== 1) Provider truth: discovery vs reasoning ==="
python3 - <<'PY'
from providers import get_all_providers
for p in get_all_providers():
    print(f"{p.metadata.type.value:10} {p.metadata.key:20} available={p.is_available()} label={p.metadata.label}")
PY

echo
echo "=== 2) Confirm /api/jobs is wired to provider fanout ==="
grep -n "fetch_provider_raw_jobs\|provider_breakdown" api/index.py || {
  echo "FAIL: api/index.py is not wired to provider fanout."
  exit 1
}

echo
echo "=== 3) Backup bridge ==="
mkdir -p .repair_backups
TS="$(date +%Y%m%d_%H%M%S)"
cp search/live_provider_bridge.py ".repair_backups/live_provider_bridge.fair.${TS}"

echo
echo "=== 4) Write fair fanout bridge ==="
cat > search/live_provider_bridge.py <<'PY'
from __future__ import annotations

import hashlib
import inspect
import logging
from typing import Any, Dict, Iterable, List

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

    search_providers = list(get_providers_by_type(ProviderType.SEARCH))
    available_providers = [p for p in search_providers if _provider_available(p)]

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

        provider_breakdown[key] = {
            "label": label,
            "available": is_available,
            "queries_attempted": 0,
            "raw_count": 0,
            "status": "ok" if is_available else "dormant",
            "cap": provider_cap,
        }

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
    }
PY

echo
echo "=== 5) Compile ==="
python3 -m py_compile $(git ls-files '*.py') search/live_provider_bridge.py

echo
echo "=== 6) Prove fairness with fake providers, no network ==="
python3 - <<'PY'
from dataclasses import dataclass
import providers
from search.live_provider_bridge import fetch_provider_raw_jobs

@dataclass
class Meta:
    key: str
    label: str
    type: object = None
    requires_api_key: bool = True

class FakeProvider:
    def __init__(self, key):
        self.metadata = Meta(key=key, label=key)

    def is_available(self):
        return True

    def search(self, query):
        return [
            {
                "title": f"{self.metadata.key} job {i} {query}",
                "company": f"{self.metadata.key} company {i}",
                "url": f"https://example.com/{self.metadata.key}/{i}",
                "snippet": "fake local proof only",
                "location": "Salt Lake City, UT",
            }
            for i in range(10)
        ]

fake_keys = ["serpapi_jobs", "serpapi_organic", "adzuna", "usajobs", "jooble", "careerjet", "themuse"]
fake = [FakeProvider(k) for k in fake_keys]

orig = providers.get_providers_by_type
providers.get_providers_by_type = lambda provider_type: fake

try:
    result = fetch_provider_raw_jobs(
        ["server jobs Salt Lake City", "cook jobs Salt Lake City", "support jobs Salt Lake City"],
        max_raw_jobs=35,
        location="Salt Lake City, UT",
    )
finally:
    providers.get_providers_by_type = orig

breakdown = result["provider_breakdown"]
print("RAW_COUNT=", len(result["raw_jobs"]))
for key in fake_keys:
    info = breakdown[key]
    print(key, info)
    assert info["available"] is True
    assert info["queries_attempted"] >= 1, f"{key} was not attempted"
    assert info["raw_count"] >= 1, f"{key} returned no raw jobs in fake proof"

assert len(result["raw_jobs"]) == 35
assert result["fair_fanout"] is True
print("PASS: every search provider is attempted before one provider can dominate.")
PY

echo
echo "=== 7) Local Flask safe proof, no live /api/jobs ==="
python3 - <<'PY'
from app import app
c = app.test_client()

for path in ["/", "/api/health", "/api/usage", "/api/jobs?dry_run=1", "/api/providers"]:
    r = c.get(path)
    print(path, r.status_code, r.content_type)
    assert r.status_code == 200

dry = c.get("/api/jobs?dry_run=1").get_json()
assert dry.get("dry_run") is True
print("PASS: safe boot proof passed.")
PY

echo
echo "=== 8) Diff proof ==="
git diff -- search/live_provider_bridge.py
git diff --check

echo
echo "DONE: fair provider fanout is fixed locally and proven. No deploy happened."
