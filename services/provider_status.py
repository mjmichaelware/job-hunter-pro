"""Provider run policy: generic, name-agnostic.

Nothing here knows the name of any specific provider. Two concerns only:

1. ENABLE/DISABLE is decided BY EACH PROVIDER in its own file via
   ``Provider.disabled_reason()`` (empty string = enabled). This module just
   exposes a safe passthrough so callers don't duplicate the try/except.

2. RUN QUARANTINE (ephemeral): a provider that returns a hard auth/rate failure
   (401/403/429) mid-run is quarantined for the REMAINDER of that run so one
   dead source can't be hammered across a large keyword fanout or poison the
   rest of discovery.

Keeping this generic is what lets the system scale to a swarm of 50+ providers
without editing any central registry/policy file.
"""

from __future__ import annotations

from typing import Any, Dict, Set

# Hard failures that should immediately quarantine a provider for the run.
HARD_FAILURE_STATUS = frozenset({401, 403, 429})


def is_hard_failure(status_code: int) -> bool:
    """True for auth/rate-limit failures that warrant quarantine."""
    try:
        return int(status_code) in HARD_FAILURE_STATUS
    except Exception:
        return False


def disabled_reason(provider: Any) -> str:
    """Provider-declared off reason ('' = enabled). Never raises."""
    fn = getattr(provider, "disabled_reason", None)
    if not callable(fn):
        return ""
    try:
        return str(fn() or "")
    except Exception:
        return ""


def is_disabled(provider: Any) -> bool:
    """True if the provider declares itself off."""
    return bool(disabled_reason(provider))


class RunQuarantine:
    """Tracks providers quarantined during a single discovery run."""

    def __init__(self) -> None:
        self._quarantined: Dict[str, str] = {}

    def quarantine(self, provider_key: str, reason: str) -> None:
        self._quarantined[provider_key] = reason

    def is_quarantined(self, provider_key: str) -> bool:
        return provider_key in self._quarantined

    def reason(self, provider_key: str) -> str:
        return self._quarantined.get(provider_key, "")

    def as_dict(self) -> Dict[str, str]:
        return dict(self._quarantined)

    @property
    def keys(self) -> Set[str]:
        return set(self._quarantined.keys())
