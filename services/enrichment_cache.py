"""
services/enrichment_cache.py

GCS-backed place enrichment cache.
Cache key = sha256(company.lower() + "|" + address.lower())[:16]
GCS path   = cache/places/{key}.json

Rules:
- In-memory dict per process for fast repeated lookups.
- GCS read-through on miss, write-back after enrichment.
- All GCS calls are best-effort: any failure -> log warning, continue.
- No secrets hardcoded; bucket name from env BATCH_BUCKET.
- Own HTTP session (cannot import from api/index.py -- circular import).
"""
import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, Optional

import requests as _req

logger = logging.getLogger("enrichment_cache")

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_mem: Dict[str, Dict[str, Any]] = {}

_token_cache: Dict[str, Any] = {
    "access_token": "",
    "expires_at": 0.0,
}

_http = _req.Session()
_http.headers.update({"User-Agent": "job-hunter-pro-enrichment-cache/1"})

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bucket() -> str:
    return os.environ.get("BATCH_BUCKET", "")


def _cache_key(company: str, address: str) -> str:
    raw = (company.lower() + "|" + address.lower()).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _access_token() -> str:
    """Return a valid GCP access token, refreshing when within 60 s of expiry."""
    now = time.monotonic()
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]
    try:
        resp = _http.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/"
            "service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"},
            timeout=2,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token", "")
        expires_in = data.get("expires_in", 3600)
        _token_cache["access_token"] = token
        _token_cache["expires_at"] = now + max(0, expires_in - 60)
        return token
    except Exception as exc:
        logger.warning("enrichment_cache: could not fetch GCP access token: %s", exc)
        return ""


def _gcs_download(object_name: str) -> Optional[Dict[str, Any]]:
    bucket = _bucket()
    if not bucket:
        return None
    token = _access_token()
    if not token:
        return None
    try:
        from urllib.parse import quote as _quote
        encoded = _quote(object_name, safe="")
        resp = _http.get(
            f"https://storage.googleapis.com/storage/v1/b/{bucket}/o/{encoded}",
            params={"alt": "media"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("enrichment_cache: GCS download failed for %s: %s", object_name, exc)
        return None


def _gcs_upload(object_name: str, data: Dict[str, Any]) -> None:
    bucket = _bucket()
    if not bucket:
        return
    token = _access_token()
    if not token:
        return
    try:
        _http.post(
            f"https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o",
            params={"uploadType": "media", "name": object_name},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            timeout=15,
        ).raise_for_status()
    except Exception as exc:
        logger.warning("enrichment_cache: GCS upload failed for %s: %s", object_name, exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def place_get(company: str, address: str) -> Dict[str, Any]:
    """Return cached enrichment fields for a (company, address) pair.

    Checks in-memory first; falls back to GCS read-through.
    Returns an empty dict if not cached or on any failure.
    """
    if not (company or address):
        return {}
    key = _cache_key(company, address)
    if key in _mem:
        return _mem[key]
    obj = f"cache/places/{key}.json"
    data = _gcs_download(obj)
    if data:
        _mem[key] = data
        return data
    return {}


def place_set(company: str, address: str, data: Dict[str, Any]) -> None:
    """Store enrichment fields for a (company, address) pair.

    Writes to in-memory and asynchronously-best-efforts to GCS.
    """
    if not (company or address) or not data:
        return
    key = _cache_key(company, address)
    _mem[key] = data
    _gcs_upload(f"cache/places/{key}.json", data)
