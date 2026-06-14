"""Provider status policy: enable/disable + per-run quarantine.

Two independent ideas live here so the rest of the system stays honest about
which sources actually ran:

1. POLICY DISABLE (persistent): some providers are intentionally off by default.
   Jooble and Careerjet repeatedly returned hard auth failures (403) upstream
   and their previously exposed credentials are treated as compromised, so they
   are disabled unless explicitly re-enabled via ``ENABLE_JOOBLE`` /
   ``ENABLE_CAREERJET`` environment flags.

2. RUN QUARANTINE (ephemeral): if a provider returns a hard auth/rate failure
   (401/403/429) during a live run, it is quarantined for the REMAINDER of that
   run so a single dead provider cannot be hammered across a large keyword
   fanout or poison the rest of the discovery flow.

No I/O. Pure policy + small stateful helper objects.
"""

from __future__ import annotations

import os
from typing import Dict, Set

# Hard failures that should immediately quarantine a provider for the run.
HARD_FAILURE_STATUS = frozenset({401, 403, 429})

# Providers disabled by default unless explicitly re-enabled by env flag.
# Mapping: provider key -> env flag that re-enables it.
POLICY_DISABLED_PROVIDERS: Dict[str, str] = {
    "jooble": "ENABLE_JOOBLE",
    "careerjet": "ENABLE_CAREERJET",
}


def _flag_enabled(flag: str) -> bool:
    return str(os.environ.get(flag, "")).strip() in {"1", "true", "True", "yes", "on"}


def is_policy_disabled(provider_key: str) -> bool:
    """True if the provider is disabled by default and not explicitly re-enabled."""
    flag = POLICY_DISABLED_PROVIDERS.get(provider_key)
    if not flag:
        return False
    return not _flag_enabled(flag)


def policy_disable_reason(provider_key: str) -> str:
    flag = POLICY_DISABLED_PROVIDERS.get(provider_key, "")
    return (
        f"disabled_by_policy (compromised/unreliable upstream; set {flag}=1 to re-enable)"
        if flag
        else ""
    )


def is_hard_failure(status_code: int) -> bool:
    """True for auth/rate-limit failures that warrant quarantine."""
    try:
        return int(status_code) in HARD_FAILURE_STATUS
    except Exception:
        return False


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
