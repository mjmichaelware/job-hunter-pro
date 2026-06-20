"""Recruitee public offers API — keyless per-company JSON.
Sweeps a configurable list of company subdomains (RECRUITEE_COMPANIES env overrides).
Default: curated list of employers known to use Recruitee, including
national employers and remote-friendly companies.
Endpoint: https://{company}.recruitee.com/api/offers/
"""
import logging
import os
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

# Curated Recruitee company subdomains (used in {slug}.recruitee.com).
# Override entirely via RECRUITEE_COMPANIES=slug1,slug2 env var.
_DEFAULT_RECRUITEE_COMPANIES = [
    "typeform",         # remote-friendly form/survey SaaS
    "miro",             # remote-friendly collaboration tool
    "contentful",       # remote-friendly headless CMS
    "phorest",          # salon software, SaaS
    "sendcloud",        # logistics SaaS, international roles
    "picnic",           # grocery tech, EU-focused but expanding
    "bolddesk",         # customer support SaaS, remote roles
    "recruitee",        # Recruitee itself posts on Recruitee
]

_env_override = os.environ.get("RECRUITEE_COMPANIES", "")
RECRUITEE_COMPANIES = [s.strip() for s in _env_override.split(",") if s.strip()] if _env_override else _DEFAULT_RECRUITEE_COMPANIES


class RecruiteeProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="recruitee",
            label="Recruitee (ATS boards)",
            type=ProviderType.SEARCH,
            description="Keyless public ATS offer boards; sweeps curated employers (override via RECRUITEE_COMPANIES).",
            requires_api_key=False,
            budget_class="free",
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return "" if RECRUITEE_COMPANIES else "RECRUITEE_COMPANIES list is empty; set RECRUITEE_COMPANIES=slug1,slug2."

    def search(self, query: str) -> List[SearchResult]:
        terms = [w for w in query.lower().split() if len(w) > 3]
        results: List[SearchResult] = []
        for company in RECRUITEE_COMPANIES:
            try:
                url = "https://%s.recruitee.com/api/offers/" % company
                resp = http_session.get(
                    url,
                    headers={"Accept": "application/json"},
                    timeout=10,
                )
                check_hard_failure(self.metadata.key, resp)
                if resp.status_code in (404, 410):
                    logger.debug("Recruitee board not found: %s", company)
                    continue
                resp.raise_for_status()
                for item in (resp.json().get("offers", []) or []):
                    title = item.get("title", "")
                    if terms and not any(t in title.lower() for t in terms):
                        continue
                    slug_job = item.get("slug", "")
                    job_url = "https://%s.recruitee.com/o/%s" % (company, slug_job) if slug_job else ""
                    location = item.get("location", "") or item.get("city", "") or ""
                    results.append(SearchResult(
                        provider=self.metadata.key,
                        query=query,
                        title=title,
                        url=job_url,
                        snippet=location or item.get("department", ""),
                        source_name=item.get("company_name", company),
                        published_date=item.get("published_at") or item.get("created_at"),
                        raw_json=item,
                        confidence=1.0,
                        cost_units=0.0,
                    ))
            except ProviderHardFailure:
                raise
            except Exception as e:
                logger.error("Recruitee company %s failed: %s", company, e)
        return results


recruitee_provider = RecruiteeProvider()
