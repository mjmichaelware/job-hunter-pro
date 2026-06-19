"""COPY-ME provider template — the one-file recipe for the 50-API swarm.

To add a new job/opportunity API to the swarm:
  1. Copy this file to providers/search/<yourname>.py  (NO leading underscore).
  2. Rename the class + change the metadata `key`/`label`/`description`.
  3. Implement search(): call the API, map each result to a SearchResult.
  4. If it needs a secret, name it (e.g. "ACME_API_KEY") and inject it ONLY via:
        bash scripts/add_key.sh ACME_API_KEY        # prompts, stores in Secret Manager
     then add it to the deploy --set-secrets list. Never hardcode the value here.
  5. Deploy. The registry auto-discovers the file — no other edits, no merge conflicts.

This file starts with "_" so the auto-discovery in providers/__init__.py SKIPS it.
A broken provider file is skipped and logged, never taking down the rest of the swarm.
"""

import logging
import os
from typing import List

from models import SearchResult
from core import http_session
from core.config import Config
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

# Per-provider tuning via env (non-secret); secrets come from Secret Manager only.
TEMPLATE_LOCATION = os.environ.get("TEMPLATE_LOCATION", "Salt Lake City, UT")


class TemplateProvider(SearchProvider):
    # The credential's Secret Manager name (set requires_api_key=False for keyless APIs).
    SECRET_NAME = "TEMPLATE_API_KEY"

    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="template",                       # unique, lower_snake
            label="Template Provider",
            type=ProviderType.SEARCH,
            description="One-file template; copy to add a real API to the swarm.",
            requires_api_key=True,                # False for keyless boards
            budget_class="free",                  # "free" or "serpapi_quota"
        )

    def is_available(self) -> bool:
        # Keyless providers: return True. Keyed: dormant until the secret exists.
        return bool(Config.provider_key(self.SECRET_NAME))

    def search(self, query: str) -> List[SearchResult]:
        api_key = Config.provider_key(self.SECRET_NAME)
        results: List[SearchResult] = []
        try:
            resp = http_session.get(
                "https://api.example.com/jobs",
                params={"q": query, "location": TEMPLATE_LOCATION, "key": api_key},
                timeout=10,
            )
            check_hard_failure(self.metadata.key, resp)   # quarantine on 401/403/429
            resp.raise_for_status()
            for item in (resp.json().get("results", []) or []):
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source_name=item.get("company", self.metadata.label),
                    published_date=item.get("posted_at"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise                                          # let the bridge quarantine it
        except Exception as e:
            logger.error("%s search failed: %s", self.metadata.key, e)
        return results


# A module-level instance is what the registry auto-discovers. Keep this line.
# (No instance here on purpose — this template must not register itself.)
# template_provider = TemplateProvider()
