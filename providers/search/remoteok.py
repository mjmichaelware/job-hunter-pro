"""RemoteOK — keyless JSON feed. https://remoteok.com/api  (needs a User-Agent)."""
import logging
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)


class RemoteOKProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="remoteok",
            label="RemoteOK",
            type=ProviderType.SEARCH,
            description="Keyless remote-jobs JSON feed.",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def search(self, query: str) -> List[SearchResult]:
        terms = [w for w in query.lower().split() if len(w) > 3]
        results: List[SearchResult] = []
        try:
            resp = http_session.get(
                "https://remoteok.com/api",
                headers={"User-Agent": "JobHunterPro/1.0 (+opportunity-intel)"},
                timeout=12,
            )
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for item in (resp.json() or []):
                # The first element is a legal/metadata object; real jobs have a position.
                if not isinstance(item, dict) or not item.get("position"):
                    continue
                title = item.get("position", "")
                hay = (title + " " + " ".join(item.get("tags", []) or [])).lower()
                if terms and not any(t in hay for t in terms):
                    continue
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=title,
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source_name=item.get("company", "RemoteOK"),
                    published_date=item.get("date"),
                    raw_json=item,
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("RemoteOK search failed: %s", e)
        return results


remoteok_provider = RemoteOKProvider()
