#!/usr/bin/env bash

# Context Anchor for Subdirectory Migration
cd "$(dirname "$0")/.."
set -euo pipefail

PROJECT_ID="ai-job-agent-498702"
REGION="us-central1"
SERVICE="job-hunter-pro"

fail(){ echo "FAIL: $1"; exit 1; }

echo "=== WIRE FEDERATED SEARCH PROVIDERS INTO /api/jobs ==="
echo "This is the backend fix: /api/jobs stops being SerpAPI-only."
echo "PWD=$(pwd)"
echo

[ -f app.py ] || fail "not in repo root"
[ -f api/index.py ] || fail "missing api/index.py"
[ -d providers/search ] || fail "missing providers/search"
[ -f providers/__init__.py ] || fail "missing providers/__init__.py"

echo "=== 1) Pre-patch proof ==="
grep -Rni "def fetch_jobs_live\|serpapi_jobs(query)\|get_providers_by_type\|ProviderType.SEARCH\|provider_breakdown" api/index.py providers search 2>/dev/null || true

echo
echo "=== 2) Backup files ==="
mkdir -p .repair_backups
TS="$(date +%Y%m%d_%H%M%S)"
cp api/index.py ".repair_backups/api.index.federated_jobs.${TS}"

echo
echo "=== 3) Create live provider bridge ==="
cat > search/live_provider_bridge.py <<'PY'
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
PY

echo
echo "=== 4) Patch api/index.py fetch_jobs_live + /api/jobs + /api/debug/jobs ==="
python3 - <<'PY'
from pathlib import Path

p = Path("api/index.py")
text = p.read_text(encoding="utf-8")

start = text.index("def fetch_jobs_live() -> Dict[str, Any]:")
end = text.index("\ndef float_arg(", start)

new_fetch = r'''def fetch_jobs_live() -> Dict[str, Any]:
    raw_jobs = []
    provider_breakdown = {}
    queries = raw_job_queries()
    query_count = len(queries)

    try:
        from search.live_provider_bridge import fetch_provider_raw_jobs
        fanout = fetch_provider_raw_jobs(
            queries,
            max_raw_jobs=Config.MAX_RAW_JOBS,
            location="Salt Lake City, UT",
        )
        raw_jobs = fanout.get("raw_jobs", [])
        provider_breakdown = fanout.get("provider_breakdown", {})
        query_count = fanout.get("query_count", query_count)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Federated provider fan-out failed; falling back to legacy SerpAPI path", exc_info=True)
        provider_breakdown = {
            "legacy_serpapi_fallback": {
                "available": True,
                "status": "fallback",
                "error": f"{type(exc).__name__}: {str(exc)[:180]}",
                "queries_attempted": 0,
                "raw_count": 0,
            }
        }

        seen_raw = set()
        for query in queries:
            provider_breakdown["legacy_serpapi_fallback"]["queries_attempted"] += 1
            for raw in serpapi_jobs(query):
                identity = clean(raw.get("job_id")) or clean(raw.get("title")) + clean(raw.get("company_name")) + clean(raw.get("location"))
                if identity and identity not in seen_raw:
                    seen_raw.add(identity)
                    raw["_query_used"] = query
                    raw["_provider"] = "legacy_serpapi"
                    raw_jobs.append(raw)
                    provider_breakdown["legacy_serpapi_fallback"]["raw_count"] += 1
                if len(raw_jobs) >= Config.MAX_RAW_JOBS:
                    break
            if len(raw_jobs) >= Config.MAX_RAW_JOBS:
                break

    accepted = []
    rejected = []
    accepted_keys = set()

    for raw in raw_jobs:
        job = normalize_job(raw)
        reasons = rejection_reasons(job)
        if reasons:
            rejected.append({
                "provider": raw.get("_provider") or raw.get("source") or raw.get("via"),
                "query": raw.get("_query_used"),
                "title": job.get("title"),
                "company": job.get("company"),
                "restaurant_name": job.get("restaurant_name"),
                "resolved_address": job.get("resolved_address"),
                "commute_label": job.get("commute_label"),
                "radius_label": job.get("radius_label"),
                "tags": job.get("tags"),
                "source_url": job.get("source_url"),
                "reasons": reasons,
            })
        else:
            key = canonical_key(job)
            if key not in accepted_keys:
                accepted_keys.add(key)
                accepted.append(job)

    accepted.sort(key=lambda j: (
        j.get("radius_miles") if j.get("radius_miles") is not None else 999,
        j.get("commute_seconds") if j.get("commute_seconds") is not None else 999999,
        -j.get("match", 0),
    ))

    return {
        "raw_count": len(raw_jobs),
        "query_count": query_count,
        "nearby_restaurant_count": len(nearby_opportunities_cached(Config.MAX_RADIUS_MILES)),
        "accepted": accepted[:30],
        "rejected": rejected[:100],
        "provider_breakdown": provider_breakdown,
    }
'''

text = text[:start] + new_fetch + text[end:]

jobs_start = text.index('@app.route("/api/jobs")')
debug_start = text.index('@app.route("/api/debug/jobs")', jobs_start)
research_start = text.index('@app.route("/api/research/place")', debug_start)

new_jobs = r'''@app.route("/api/jobs")
def jobs():
    if request.args.get("dry_run") == "1":
        return jsonify({
            "status": "ok",
            "dry_run": True,
            "message": "Live jobs endpoint is available. This dry run did not spend discovery provider budget.",
            "max_serp_queries": Config.MAX_SERP_QUERIES,
            "budget": serpapi_account_status(),
        })

    result = fetch_jobs_live()
    filtered = apply_filters(result["accepted"])

    rejection_summary = {}
    for item in result.get("rejected", []):
        for reason in item.get("reasons", []):
            rejection_summary[reason] = rejection_summary.get(reason, 0) + 1

    return jsonify({
        "status": "success",
        "source": VERSION,
        "count": len(filtered),
        "unfiltered_count": len(result["accepted"]),
        "raw_count": result["raw_count"],
        "query_count": result["query_count"],
        "nearby_restaurant_count": result["nearby_restaurant_count"],
        "rejected_count": len(result.get("rejected", [])),
        "rejection_summary": rejection_summary,
        "provider_breakdown": result.get("provider_breakdown", {}),
        "rules": {
            "origin": Config.ORIGIN_ADDRESS,
            "max_radius_miles": Config.MAX_RADIUS_MILES,
            "max_transit_minutes": round(Config.MAX_TRANSIT_SECONDS / 60),
            "food_only": True,
            "discovery": "federated_search_providers",
            "reasoning_providers": "not_used_as_discovery",
        },
        "data": filtered,
        "rejected": result.get("rejected", [])[:100],
    })

@app.route("/api/debug/jobs")
def debug_jobs():
    result = fetch_jobs_live()
    return jsonify({
        "status": "success",
        "source": VERSION,
        "accepted_count": len(result["accepted"]),
        "rejected_count": len(result["rejected"]),
        "raw_count": result["raw_count"],
        "query_count": result["query_count"],
        "nearby_restaurant_count": result["nearby_restaurant_count"],
        "provider_breakdown": result.get("provider_breakdown", {}),
        "accepted": result["accepted"],
        "rejected": result["rejected"],
    })

'''

text = text[:jobs_start] + new_jobs + text[research_start:]
p.write_text(text, encoding="utf-8")
print("api/index.py patched")
PY

echo
echo "=== 5) Post-patch inspection ==="
grep -Rni "fetch_provider_raw_jobs\|provider_breakdown\|federated_search_providers\|reasoning_providers\|legacy_serpapi_fallback" api/index.py search/live_provider_bridge.py

echo
echo "=== 6) Compile all Python ==="
python3 -m py_compile $(git ls-files '*.py') search/live_provider_bridge.py

echo
echo "=== 7) Local proof without live /api/jobs ==="
python3 - <<'PY'
from app import app

c = app.test_client()

for path in ["/", "/api/health", "/api/usage", "/api/jobs?dry_run=1", "/api/providers"]:
    r = c.get(path)
    print(path, r.status_code, r.content_type)
    assert r.status_code == 200

source = open("api/index.py", encoding="utf-8").read()
assert "fetch_provider_raw_jobs" in source
assert "provider_breakdown" in source
assert "federated_search_providers" in source

bridge = open("search/live_provider_bridge.py", encoding="utf-8").read()
assert "get_providers_by_type(ProviderType.SEARCH)" in bridge
assert "Reasoning" not in bridge

print("PASS: /api/jobs is wired to SEARCH provider fan-out, not LLM discovery.")
PY

echo
echo "=== 8) Diff proof ==="
git diff -- api/index.py search/live_provider_bridge.py
git diff --check

echo
echo "=== 9) Commit and push ==="
git add api/index.py search/live_provider_bridge.py
git commit -m "Wire federated search providers into live jobs"
git push origin main

echo
echo "=== 10) Wait for deploy trigger ==="
sleep 120

echo
echo "=== 11) Verify Cloud Run health ==="
SERVICE_URL="$(gcloud run services describe "$SERVICE" --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')"
echo "SERVICE_URL=$SERVICE_URL"

gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format="table(status.url,status.latestReadyRevisionName,status.traffic[0].revisionName,status.traffic[0].percent)"

curl -fsS "$SERVICE_URL/api/health"
echo

echo
echo "=== 12) Live provider status ==="
curl -fsS "$SERVICE_URL/api/providers" -o data/live_providers_after_fanout.json
python3 - <<'PY'
import json
data = json.load(open("data/live_providers_after_fanout.json"))
providers = data.get("providers", [])
for p in providers:
    if p.get("type") == "search":
        print(p.get("key"), "available=", p.get("is_available"), "requires_key=", p.get("requires_api_key"))
PY

echo
echo "=== 13) ONE LIVE /api/jobs FAN-OUT PROOF — may use discovery provider budget ==="
OUT="./data/live_jobs_federated_now.json"
rm -f "$OUT"
curl -sS "$SERVICE_URL/api/jobs" -o "$OUT" -w "HTTP %{http_code}\n"

python3 - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("data/live_jobs_federated_now.json").read_text())
print("TOP_KEYS=", sorted(data.keys()))
for key in ["status", "count", "unfiltered_count", "raw_count", "query_count", "rejected_count", "nearby_restaurant_count"]:
    print(f"{key}=", data.get(key))

print()
print("PROVIDER_BREAKDOWN:")
for key, info in (data.get("provider_breakdown") or {}).items():
    print(key, info)

print()
print("rejection_summary=", data.get("rejection_summary"))
print("data_len=", len(data.get("data", [])))
print("rejected_len=", len(data.get("rejected", [])))

if data.get("data"):
    first = data["data"][0]
    print("FIRST_ACCEPTED_KEYS=", sorted(first.keys()))
    print("FIRST_ACCEPTED_TITLE=", first.get("title"))
    print("FIRST_ACCEPTED_COMPANY=", first.get("company"))
elif data.get("rejected"):
    first = data["rejected"][0]
    print("FIRST_REJECTED_TITLE=", first.get("title"))
    print("FIRST_REJECTED_PROVIDER=", first.get("provider"))
    print("FIRST_REJECTED_REASONS=", first.get("reasons"))
PY

echo
echo "OPEN:"
echo "$SERVICE_URL/?v=federated-jobs-$(date +%s)"
