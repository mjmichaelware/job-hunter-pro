"""Workable public ATS widget API — keyless per-company JSON.
Sweeps a configurable list of company slugs (WORKABLE_BOARDS env overrides).
Default: curated list of employers known to use Workable, including several
with SLC/Utah presence and national employers with remote roles.
Endpoint: https://apply.workable.com/api/v1/widget/accounts/{slug}/jobs
"""
import logging
import os
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

# Curated Workable company slugs (public board slugs used in apply.workable.com URLs).
# Override entirely via WORKABLE_BOARDS=slug1,slug2 env var.
_DEFAULT_WORKABLE_BOARDS = [
    "numberly",         # marketing tech company, remote-friendly
    "epignosis",        # eLearning / TalentLMS, remote-friendly
    "blueground",       # furnished apartments / hospitality, US cities incl SLC area
    "personio",         # HR SaaS, US presence
    "workable",         # Workable itself posts on Workable
    "taxjar",           # Salt Lake City, UT HQ (TaxJar/Stripe)
    "backcountry",      # Park City, UT — outdoor retail, major UT employer
    "skullcandy",       # Park City, UT — audio brand
    "instructure",      # Salt Lake City, UT HQ — Canvas LMS large employer
    "chatfuel",         # remote-friendly SaaS
]

_env_override = os.environ.get("WORKABLE_BOARDS", "")
WORKABLE_BOARDS = [s.strip() for s in _env_override.split(",") if s.strip()] if _env_override else _DEFAULT_WORKABLE_BOARDS


class WorkableProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="workable",
            label="Workable (ATS boards)",
            type=ProviderType.SEARCH,
            description="Keyless public ATS boards; sweeps curated employer slugs (override via WORKABLE_BOARDS).",
            requires_api_key=False,
            budget_class="free",
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return "" if WORKABLE_BOARDS else "WORKABLE_BOARDS list is empty; set WORKABLE_BOARDS=slug1,slug2."

    def search(self, query: str) -> List[SearchResult]:
        terms = [w for w in query.lower().split() if len(w) > 3]
        results: List[SearchResult] = []
        for slug in WORKABLE_BOARDS:
            try:
                url = "https://apply.workable.com/api/v1/widget/accounts/%s/jobs" % slug
                resp = http_session.get(
                    url,
                    headers={"Accept": "application/json"},
                    timeout=10,
                )
                check_hard_failure(self.metadata.key, resp)
                if resp.status_code == 404:
                    logger.debug("Workable board not found: %s", slug)
                    continue
                resp.raise_for_status()
                for item in (resp.json().get("results", []) or []):
                    title = item.get("title", "")
                    if terms and not any(t in title.lower() for t in terms):
                        continue
                    location = item.get("location", {}) or {}
                    loc_str = ", ".join(filter(None, [
                        location.get("city", ""),
                        location.get("region", ""),
                        location.get("country", ""),
                    ]))
                    job_url = "https://apply.workable.com/%s/j/%s/" % (slug, item.get("shortcode", ""))
                    results.append(SearchResult(
                        provider=self.metadata.key,
                        query=query,
                        title=title,
                        url=job_url,
                        snippet=loc_str or item.get("department", ""),
                        source_name=slug,
                        published_date=item.get("published_on") or item.get("created_at"),
                        raw_json=item,
                        confidence=1.0,
                        cost_units=0.0,
                    ))
            except ProviderHardFailure:
                raise
            except Exception as e:
                logger.error("Workable board %s failed: %s", slug, e)
        return results


workable_provider = WorkableProvider()
