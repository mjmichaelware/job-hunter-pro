#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ID = "ai-job-agent-498702"
OUT_DIR = Path("audits")
OUT_DIR.mkdir(exist_ok=True)

SECRET_NAMES = [
    "SERPAPI_KEY",
    "GOOGLE_MAPS_API_KEY",
    "ADZUNA_APP_ID",
    "ADZUNA_APP_KEY",
    "USAJOBS_API_KEY",
    "USAJOBS_EMAIL",
    "JOOBLE_API_KEY",
    "CAREERJET_AFFID",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GROQ_API_KEY",
    "XAI_API_KEY",
]

def get_secret(name: str) -> tuple[bool, str]:
    r = subprocess.run(
        [
            "gcloud", "secrets", "versions", "access", "latest",
            "--secret", name,
            "--project", PROJECT_ID,
        ],
        text=True,
        capture_output=True,
    )
    if r.returncode != 0:
        return False, ""
    return True, r.stdout.rstrip("\n")

def request_json(name: str, method: str, url: str, headers=None, body=None, timeout=20) -> dict:
    headers = headers or {}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers = {**headers, "Content-Type": "application/json"}

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(3000).decode("utf-8", errors="ignore")
            elapsed_ms = round((time.time() - started) * 1000)
            parsed = None
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = None
            return {
                "name": name,
                "ok": 200 <= resp.status < 300,
                "status": resp.status,
                "elapsed_ms": elapsed_ms,
                "summary": summarize(name, parsed, raw),
            }
    except urllib.error.HTTPError as e:
        raw = e.read(1200).decode("utf-8", errors="ignore")
        return {
            "name": name,
            "ok": False,
            "status": e.code,
            "elapsed_ms": round((time.time() - started) * 1000),
            "summary": raw[:500],
        }
    except Exception as e:
        return {
            "name": name,
            "ok": False,
            "status": "ERROR",
            "elapsed_ms": round((time.time() - started) * 1000),
            "summary": repr(e)[:500],
        }

def summarize(name: str, parsed, raw: str) -> str:
    if isinstance(parsed, dict):
        if name == "SerpAPI Account":
            return "account payload received; keys not printed"
        if name == "Adzuna":
            return f"count={parsed.get('count', 'unknown')}"
        if name == "USAJOBS":
            sr = parsed.get("SearchResult") or {}
            return f"count={sr.get('SearchResultCount', 'unknown')} total={sr.get('SearchResultCountAll', 'unknown')}"
        if name == "Jooble":
            return f"totalCount={parsed.get('totalCount', 'unknown')}"
        if name == "Careerjet":
            return f"type={parsed.get('type', 'unknown')} hits={parsed.get('hits', 'unknown')}"
        if name == "The Muse":
            return f"results={len(parsed.get('results', []) or [])}"
        if name in {"OpenAI", "Groq", "xAI"}:
            data = parsed.get("data")
            return f"models={len(data) if isinstance(data, list) else 'unknown'}"
        if name == "Gemini":
            models = parsed.get("models")
            return f"models={len(models) if isinstance(models, list) else 'unknown'}"
        if name == "Anthropic":
            data = parsed.get("data")
            return f"models={len(data) if isinstance(data, list) else 'unknown'}"
        if name == "Google Maps Geocode":
            return f"status={parsed.get('status', 'unknown')}"
    return raw[:300].replace("\n", " ")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["inventory", "live"], default="inventory")
    ap.add_argument("--confirm-live-provider-probes", action="store_true")
    args = ap.parse_args()

    if args.mode == "live" and not args.confirm_live_provider_probes:
        print("ERROR: live mode may use provider quota. Re-run with --confirm-live-provider-probes.")
        return 2

    secrets = {}
    results = []

    print("Secret Manager access check:")
    missing = []
    for name in SECRET_NAMES:
        ok, value = get_secret(name)
        print(f"  {name}: {'OK' if ok and value else 'MISSING_OR_EMPTY'}")
        if ok and value:
            secrets[name] = value
        else:
            missing.append(name)

    # No-key public probe.
    results.append(request_json(
        "The Muse Optional",
        "GET",
        "https://www.themuse.com/api/public/jobs?page=0",
        headers={
            "User-Agent": "JobHunterPro/1.0 provider-readiness-check",
            "Accept": "application/json",
        },
    ))

    # SerpAPI account check is safer than a search query.
    if "SERPAPI_KEY" in secrets:
        results.append(request_json(
            "SerpAPI Account",
            "GET",
            "https://serpapi.com/account.json?" + urllib.parse.urlencode({"api_key": secrets["SERPAPI_KEY"]}),
        ))

    if args.mode == "live":
        # Discovery provider probes: intentionally tiny.
        if "ADZUNA_APP_ID" in secrets and "ADZUNA_APP_KEY" in secrets:
            results.append(request_json(
                "Adzuna",
                "GET",
                "https://api.adzuna.com/v1/api/jobs/us/search/1?" + urllib.parse.urlencode({
                    "app_id": secrets["ADZUNA_APP_ID"],
                    "app_key": secrets["ADZUNA_APP_KEY"],
                    "results_per_page": "1",
                    "what": "server",
                    "where": "Salt Lake City",
                }),
            ))

        if "USAJOBS_API_KEY" in secrets and "USAJOBS_EMAIL" in secrets:
            results.append(request_json(
                "USAJOBS",
                "GET",
                "https://data.usajobs.gov/api/Search?" + urllib.parse.urlencode({
                    "Keyword": "server",
                    "LocationName": "Salt Lake City, Utah",
                    "ResultsPerPage": "1",
                    "WhoMayApply": "public",
                }),
                headers={
                    "Host": "data.usajobs.gov",
                    "User-Agent": secrets["USAJOBS_EMAIL"],
                    "Authorization-Key": secrets["USAJOBS_API_KEY"],
                },
            ))

        if "JOOBLE_API_KEY" in secrets:
            results.append(request_json(
                "Jooble",
                "POST",
                "https://jooble.org/api/" + urllib.parse.quote(secrets["JOOBLE_API_KEY"]),
                body={
                    "keywords": "server",
                    "location": "Salt Lake City",
                    "page": 1,
                },
            ))

        if "CAREERJET_AFFID" in secrets:
            import base64
            careerjet_basic = base64.b64encode((secrets["CAREERJET_AFFID"] + ":").encode("utf-8")).decode("ascii")
            results.append(request_json(
                "Careerjet",
                "GET",
                "https://search.api.careerjet.net/v4/query?" + urllib.parse.urlencode({
                    "locale_code": "en_US",
                    "keywords": "server",
                    "location": "Salt Lake City",
                    "fragment_size": "80",
                }),
                headers={
                    "Authorization": "Basic " + careerjet_basic,
                    "Accept": "application/json",
                    "User-Agent": "JobHunterPro/1.0 provider-readiness-check",
                },
            ))

        if "GOOGLE_MAPS_API_KEY" in secrets:
            results.append(request_json(
                "Google Maps Geocode",
                "GET",
                "https://maps.googleapis.com/maps/api/geocode/json?" + urllib.parse.urlencode({
                    "address": "Salt Lake City, UT",
                    "key": secrets["GOOGLE_MAPS_API_KEY"],
                }),
            ))

        # Reasoning/model-list probes. These do not generate completions.
        if "OPENAI_API_KEY" in secrets:
            results.append(request_json(
                "OpenAI",
                "GET",
                "https://api.openai.com/v1/models",
                headers={"Authorization": "Bearer " + secrets["OPENAI_API_KEY"]},
            ))

        if "GEMINI_API_KEY" in secrets:
            results.append(request_json(
                "Gemini",
                "GET",
                "https://generativelanguage.googleapis.com/v1beta/models?" + urllib.parse.urlencode({
                    "key": secrets["GEMINI_API_KEY"],
                }),
            ))

        if "ANTHROPIC_API_KEY" in secrets:
            results.append(request_json(
                "Anthropic",
                "GET",
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": secrets["ANTHROPIC_API_KEY"],
                    "anthropic-version": "2023-06-01",
                },
            ))

        if "GROQ_API_KEY" in secrets:
            results.append(request_json(
                "Groq",
                "GET",
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": "Bearer " + secrets["GROQ_API_KEY"]},
            ))

        if "XAI_API_KEY" in secrets:
            results.append(request_json(
                "xAI",
                "GET",
                "https://api.x.ai/v1/models",
                headers={"Authorization": "Bearer " + secrets["XAI_API_KEY"]},
            ))

    print()
    print("Probe results:")
    failures = []
    for r in results:
        status = "OK" if r["ok"] else "FAIL"
        print(f"  {status} {r['name']} status={r['status']} elapsed_ms={r['elapsed_ms']} summary={r['summary']}")
        if not r["ok"] and r["name"] != "The Muse Optional":
            failures.append(r)
        elif not r["ok"] and r["name"] == "The Muse Optional":
            print("    REVIEW: The Muse is no-key optional and may block Termux/CDN probes; not deploy-blocking.")

    out = OUT_DIR / f"s12_provider_probe_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps({
        "mode": args.mode,
        "missing_or_empty_secrets": missing,
        "results": results,
        "pass": not missing and not failures,
        "note": "No secret values are stored in this report.",
    }, indent=2), encoding="utf-8")

    print()
    print(f"Report: {out}")
    if missing:
        print("Missing/empty secrets:", ", ".join(missing))
    if failures:
        print("RESULT: FAIL/REVIEW. One or more probes failed.")
        return 2

    print("RESULT: PASS for selected probe mode.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
