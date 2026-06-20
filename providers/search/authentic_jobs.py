"""Authentic Jobs RSS feed — keyless.

Endpoint: https://authenticjobs.com/?keywords={query}&location=Utah&format=rss
Parses RSS: item -> title, link, description, pubDate
"""
import logging
import xml.etree.ElementTree as ET
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

log = logging.getLogger(__name__)

_BASE_URL = "https://authenticjobs.com/"


class AuthenticJobsProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="authentic_jobs",
            label="Authentic Jobs",
            type=ProviderType.SEARCH,
            description="Curated professional and creative job listings",
            requires_api_key=False,
            budget_class="free",
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return ""

    def search(self, query: str, location: str = "", limit: int = 50) -> List[SearchResult]:
        results: List[SearchResult] = []
        try:
            params = {
                "keywords": query.strip(),
                "location": location.strip() or "Utah",
                "format": "rss",
            }
            resp = http_session.get(_BASE_URL, params=params, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")
            for item in items[:limit]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                description = (item.findtext("description") or "").strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                if not title or not link:
                    continue
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=title,
                    url=link,
                    snippet=description[:300] if description else None,
                    source_name="Authentic Jobs",
                    published_date=pub_date or None,
                    raw_json={"title": title, "link": link, "description": description, "pubDate": pub_date},
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            log.error("AuthenticJobs search failed: %s", e)
        return results


authentic_jobs_provider = AuthenticJobsProvider()
