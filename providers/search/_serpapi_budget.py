"""Shared SerpAPI budget guard (underscore -> not a discoverable provider).

SerpAPI is the one paid, quota-scarce discovery source. Both SerpAPI providers
call ``allows_search()`` before spending. If remaining searches are at/under the
configured floor, they skip — protecting quota even when broad caps are high.

The account check (account.json) does NOT count as a search and is cached for a
short window so a single run doesn't hammer it.
"""

from __future__ import annotations

import os
import time
from typing import Optional

from core import Config, http_session

_CACHE: dict = {"ts": 0.0, "left": None}
_TTL_SECONDS = float(os.environ.get("SERPAPI_ACCOUNT_TTL", "120"))


def searches_left() -> Optional[int]:
    """Remaining SerpAPI searches (cached). None if unknown/unavailable."""
    if not Config.SERPAPI_KEY:
        return None
    now = time.time()
    if _CACHE["left"] is not None and (now - _CACHE["ts"]) < _TTL_SECONDS:
        return _CACHE["left"]
    try:
        res = http_session.get(
            "https://serpapi.com/account.json",
            params={"api_key": Config.SERPAPI_KEY},
            timeout=Config.REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        left = res.json().get("total_searches_left")
        left = int(left) if left is not None else None
    except Exception:
        left = None
    _CACHE["ts"] = now
    _CACHE["left"] = left
    return left


def allows_search() -> bool:
    """True if it is safe to spend a SerpAPI search right now."""
    if not Config.SERPAPI_KEY:
        return False
    if not getattr(Config, "SERPAPI_BUDGET_MODE", True):
        return True
    left = searches_left()
    if left is None:
        # Unknown budget -> be conservative but not blocking; allow.
        return True
    floor = int(getattr(Config, "SERPAPI_MIN_SEARCHES_LEFT", 40))
    return left > floor
