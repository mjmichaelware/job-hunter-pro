"""Radius-based locality filter for discovery (origin: 28 E Bryan Ave, SLC 84115).

No hardcoded country/city blocklists drive the decision. The filter is:

  1. If the job already has a computed ``radius_miles`` (Google Places /
     Haversine), keep it only when within ``MAX_RADIUS_MILES`` (default 5).
  2. Otherwise geocode the location text (free Photon, Nominatim fallback,
     in-process cache + per-run budget) and keep it only when its distance to
     the 84115 origin is within the radius. Berlin, Paris, New York, Provo,
     Sandy — all excluded by distance, no lists required.
  3. If geocoding is unavailable/unreachable, fall back to requiring a Salt
     Lake City / South Salt Lake signal ("salt lake", "slc") or a bare street
     address, per the user's address-less rule.

This module contains no foreign-country or out-of-state name lists.
"""

from __future__ import annotations

import math
import os
import re
import threading
from typing import Any, Dict, Optional, Tuple

from core import http_session

# 84115 origin (28 E Bryan Ave, Salt Lake City, UT).
ORIGIN_LATLNG = (40.7106, -111.8867)

_UA = "JobHunterPro/1.0 (local job radius filter; contact: app owner)"

_STREET_SUFFIX = (
    r"(?:st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|way|ct|court|"
    r"ln|lane|pkwy|parkway|hwy|highway|cir|circle|pl|place|ter|terrace|"
    r"suite|ste|unit|#)"
)
_STREET_ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+[nesw]?\s*[a-z0-9.' -]{2,40}\b" + _STREET_SUFFIX + r"\b", re.I
)
_GRID_ADDRESS_RE = re.compile(r"\b\d{1,6}\s+[nesw]\s+\d{1,6}\s+[nesw]\b", re.I)
_MORE_SUFFIX_RE = re.compile(r"\s*\(\+\d+\s*more\)\s*$", re.I)

_geo_lock = threading.Lock()
_geo_cache: Dict[str, Optional[Tuple[float, float]]] = {}
_geo_budget = {"remaining": 120}
_MAX_CACHE = 5000
_STORE_MISS = object()


def _sqlite_get(query: str):
    """Persisted geocode cache lookup (survives process restarts)."""
    try:
        from store.sqlite_repo import get_sqlite_cache_repo

        repo = get_sqlite_cache_repo(os.environ.get("JHP_SQLITE_DB", "/tmp/job_hunter_pro.sqlite"))
        doc = repo.get("geo|" + query)
        if doc is None:
            return _STORE_MISS
        coords = doc.get("coords")
        return tuple(coords) if coords else None
    except Exception:
        return _STORE_MISS


def _sqlite_put(query: str, coords: Optional[Tuple[float, float]]) -> None:
    try:
        from store.sqlite_repo import get_sqlite_cache_repo

        repo = get_sqlite_cache_repo(os.environ.get("JHP_SQLITE_DB", "/tmp/job_hunter_pro.sqlite"))
        repo.save("geo|" + query, {"q": query, "coords": list(coords) if coords else None})
    except Exception:
        pass


def set_geocode_budget(remaining: int) -> None:
    """Per-run budget for NEW geocode lookups (cache hits are always free)."""
    with _geo_lock:
        _geo_budget["remaining"] = max(0, int(remaining))


def local_gate_enabled() -> bool:
    """LOCAL_LOCATION_GATE=0 disables the whole locality gate."""
    return os.environ.get("LOCAL_LOCATION_GATE", "1").strip().lower() not in {
        "0", "false", "no", "off",
    }


def _normalize_query(location: Any) -> str:
    text = re.sub(r"\s+", " ", str(location or "")).strip()
    text = _MORE_SUFFIX_RE.sub("", text)
    text = text.strip(" ,;-")
    return text[:140]


def _lookup_photon(query: str) -> Optional[Tuple[float, float]]:
    try:
        response = http_session.get(
            "https://photon.komoot.io/api/",
            params={"q": query, "limit": 1},
            headers={"User-Agent": _UA},
            timeout=6,
        )
        if response.status_code != 200:
            return None
        features = response.json().get("features") or []
        if not features:
            return None
        coords = (features[0].get("geometry") or {}).get("coordinates") or []
        if len(coords) >= 2:
            return float(coords[1]), float(coords[0])
    except Exception:
        return None
    return None


def _lookup_nominatim(query: str) -> Optional[Tuple[float, float]]:
    try:
        response = http_session.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": _UA},
            timeout=8,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None
    return None


def geocode_location(location: Any) -> Optional[Tuple[float, float]]:
    """Geocode a location string with memory + SQLite cache and a per-run budget."""
    query = _normalize_query(location)
    if not query:
        return None
    with _geo_lock:
        if query in _geo_cache:
            return _geo_cache[query]

    stored = _sqlite_get(query)
    if stored is not _STORE_MISS:
        with _geo_lock:
            _geo_cache[query] = stored
        return stored

    with _geo_lock:
        if _geo_budget["remaining"] <= 0:
            return None
        _geo_budget["remaining"] -= 1

    coords = _lookup_photon(query) or _lookup_nominatim(query)

    with _geo_lock:
        if len(_geo_cache) >= _MAX_CACHE:
            try:
                _geo_cache.pop(next(iter(_geo_cache)))
            except Exception:
                _geo_cache.clear()
        _geo_cache[query] = coords
    _sqlite_put(query, coords)
    return coords


def _text_fallback_looks_local(location: str) -> bool:
    """Strict fallback when geocoding is unavailable: Salt Lake City / South
    Salt Lake only (the city segment must start with them), "slc", or a bare
    street address. "Sandy, Salt Lake County" does NOT pass."""
    loc = re.sub(r"\s+", " ", str(location or "")).strip().lower()
    if not loc:
        return False
    if re.search(r"(?<![a-z])slc(?![a-z])", loc):
        return True
    if loc.startswith("salt lake city") or loc.startswith("south salt lake"):
        return True
    if _STREET_ADDRESS_RE.search(loc) or _GRID_ADDRESS_RE.search(loc):
        return True
    return False


def haversine_miles(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    radius = 3958.7613
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def job_within_local_radius(job: dict, max_radius_miles) -> bool:
    """True when the job is inside the radius (geocoded), per the rules above."""
    try:
        limit = float(max_radius_miles)
    except (TypeError, ValueError):
        return True
    if limit <= 0:
        return True

    for key in ("radius_miles", "distance_miles"):
        radius = job.get(key)
        if radius is not None:
            try:
                return float(radius) <= limit
            except (TypeError, ValueError):
                continue

    location = (
        job.get("resolved_address")
        or job.get("location")
        or job.get("listing_location")
        or ""
    )
    coords = geocode_location(location)
    if coords:
        try:
            return haversine_miles(ORIGIN_LATLNG, coords) <= limit
        except Exception:
            pass
    # Geocoder unavailable or unknown place: address-less fallback rule.
    return _text_fallback_looks_local(location)
