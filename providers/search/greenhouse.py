"""Greenhouse public Boards API — keyless per-company JSON.
Sweeps a configurable list of employer slugs (GREENHOUSE_BOARDS env overrides).
Default: a curated list of employers known to be on Greenhouse, including several
with SLC/Utah operations and large national employers that hire locally.
Endpoint: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
"""
import logging
import os
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

# Curated list of well-known Greenhouse board slugs. These are public, verified slugs
# for employers with known Greenhouse boards (Utah-area and large national employers).
# Override entirely via GREENHOUSE_BOARDS=slug1,slug2 env var.
_DEFAULT_GREENHOUSE_BOARDS = [
    "qualtrics",        # Provo, UT HQ — major SLC-area tech employer
    "pluralsight",      # Draper, UT HQ — Utah tech employer
    "domo",             # American Fork, UT HQ
    "podium",           # Lehi, UT — Utah tech company
    "lucid",            # South Jordan, UT — Lucid Software
    "healthequity",     # Draper, UT — large Utah employer
    "ancestry",         # Lehi, UT — Ancestry.com
    "entrata",          # Lehi, UT — property management tech
    "riverbedtechnology",  # national, remote-friendly tech
    "doordash",         # large national employer, delivers in SLC
    "twilio",           # national, remote-friendly
    "coinbase",         # national, remote-friendly
    "brex",             # national, remote-friendly fintech
    "zapier",           # fully remote — strong remote jobs source
    "figma",            # national design tool company
]

_env_override = os.environ.get("GREENHOUSE_BOARDS", "")
GREENHOUSE_BOARDS = [s.strip() for s in _env_override.split(",") if s.strip()] if _env_override else _DEFAULT_GREENHOUSE_BOARDS


class GreenhouseProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="greenhouse",
            label="Greenhouse (ATS boards)",
            type=ProviderType.SEARCH,
            description="Keyless public ATS boards; sweeps curated employer slugs (override via GREENHOUSE_BOARDS).",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True  # keyless; default slug list always active

    def disabled_reason(self) -> str:
        return "" if GREENHOUSE_BOARDS else "GREENHOUSE_BOARDS list is empty; set GREENHOUSE_BOARDS=slug1,slug2."

    def search(self, query: str) -> List[SearchResult]:
        terms = [w for w in query.lower().split() if len(w) > 3]
        results: List[SearchResult] = []
        for slug in GREENHOUSE_BOARDS:
            try:
                url = "https://boards-api.greenhouse.io/v1/boards/%s/jobs?content=true" % slug
                resp = http_session.get(url, timeout=10)
                check_hard_failure(self.metadata.key, resp)
                resp.raise_for_status()
                for item in (resp.json().get("jobs", []) or []):
                    title = item.get("title", "")
                    if terms and not any(t in title.lower() for t in terms):
                        continue
                    loc = (item.get("location") or {}).get("name", "")
                    results.append(SearchResult(
                        provider=self.metadata.key,
                        query=query,
                        title=title,
                        url=item.get("absolute_url", ""),
                        snippet=loc,
                        source_name=slug,
                        published_date=item.get("updated_at"),
                        raw_json=item,
                        confidence=1.0,
                        cost_units=0.0,
                    ))
            except ProviderHardFailure:
                raise
            except Exception as e:
                logger.error("Greenhouse board %s failed: %s", slug, e)
        return results


greenhouse_provider = GreenhouseProvider()
