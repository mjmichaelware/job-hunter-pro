"""Craigslist Salt Lake City jobs RSS — keyless.

Endpoint: https://saltlakecity.craigslist.org/search/jjj?format=rss&query={query}
Parses RSS XML: channel > item -> title, link, description, pubDate
"""
import logging
import xml.etree.ElementTree as ET
from typing import List
from urllib.parse import quote_plus

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

log = logging.getLogger(__name__)

_BASE_URL = "https://saltlakecity.craigslist.org/search/jjj"
_NS = "http://purl.org/rss/1.0/"


class CraigslistSLCProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="craigslist_slc",
            label="Craigslist SLC",
            type=ProviderType.SEARCH,
            description="Local Salt Lake City jobs from Craigslist (food service, gigs, part-time)",
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
            params = {"format": "rss"}
            if query.strip():
                params["query"] = query.strip()
            resp = http_session.get(_BASE_URL, params=params, timeout=12)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            # RSS can use default or namespaced elements
            items = root.findall(".//item")
            if not items:
                items = root.findall(".//{%s}item" % _NS)
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
                    source_name="Craigslist SLC",
                    published_date=pub_date or None,
                    raw_json={"title": title, "link": link, "description": description, "pubDate": pub_date},
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            log.error("Craigslist SLC search failed: %s", e)
        return results


craigslist_slc_provider = CraigslistSLCProvider()
