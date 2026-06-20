"""Data.SLC.gov (Socrata) — Salt Lake City employer/permit LEADS (not postings).
Keyless (optional DATA_SLC_APP_TOKEN). ON by default; opt-out via DISABLE_DATA_SLC=1.
Configure DATA_SLC_DATASET to override the dataset Socrata 4x4 id.
Default dataset: tqyd-wbgu (SLC business licenses, filtered to active Food & Bev/Retail).
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

# SLC Business License dataset (Socrata 4x4). Well-known, publicly documented.
# Override via DATA_SLC_DATASET env var if you need a different dataset.
DATASET = os.environ.get("DATA_SLC_DATASET", "tqyd-wbgu")


class DataSlcProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="data_slc",
            label="Data.SLC.gov (employer leads)",
            type=ProviderType.SEARCH,
            description="SLC open-data employer/permit leads (set DATA_SLC_DATASET).",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        # ON by default; opt-out by setting DISABLE_DATA_SLC=1.
        if os.environ.get("DISABLE_DATA_SLC"):
            return "Disabled via DISABLE_DATA_SLC env flag."
        if not DATASET:
            return "Set DATA_SLC_DATASET=<socrata-4x4-id> to choose a dataset."
        return ""

    def search(self, query: str) -> List[SearchResult]:
        if not DATASET:
            return []
        params = {"$limit": 50}
        if query.strip():
            params["$q"] = query.strip()
        headers = {}
        tok = Config.provider_key("DATA_SLC_APP_TOKEN")
        if tok:
            headers["X-App-Token"] = tok
        results: List[SearchResult] = []
        try:
            url = "https://data.slc.gov/resource/%s.json" % DATASET
            resp = http_session.get(url, params=params, headers=headers, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for row in (resp.json() or []):
                name = row.get("business_name") or row.get("name") or row.get("dba") or ""
                if not name:
                    continue
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title="Employer lead: %s" % name,
                    url="https://data.slc.gov/resource/%s.json" % DATASET,
                    snippet=str(row.get("address") or row.get("location") or ""),
                    source_name=name,
                    published_date=None,
                    raw_json=row,
                    confidence=0.5,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("Data.SLC.gov failed: %s", e)
        return results


data_slc_provider = DataSlcProvider()
