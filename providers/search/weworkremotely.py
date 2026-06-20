"""We Work Remotely RSS feed — keyless. https://weworkremotely.com/remote-jobs.rss

Parses the public RSS feed for real remote job listings. No key required.
"""
import logging
import xml.etree.ElementTree as ET
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

_RSS_URL = "https://weworkremotely.com/remote-jobs.rss"


class WeWorkRemotelyProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="weworkremotely",
            label="We Work Remotely",
            type=ProviderType.SEARCH,
            description="Keyless RSS feed of real remote job listings.",
            requires_api_key=False,
            budget_class="free",
        )

    def is_available(self) -> bool:
        return True

    def search(self, query: str) -> List[SearchResult]:
        terms = [w for w in query.lower().split() if len(w) > 2]
        results: List[SearchResult] = []
        try:
            resp = http_session.get(
                _RSS_URL,
                headers={"User-Agent": "JobHunterPro/1.0 (+opportunity-intel)"},
                timeout=12,
            )
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
            for item in root.findall(".//item"):
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")
                pub_el = item.find("pubDate")
                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                link = link_el.text.strip() if link_el is not None and link_el.text else ""
                desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
                pub_date = pub_el.text.strip() if pub_el is not None and pub_el.text else ""
                if not title:
                    continue
                hay = (title + " " + desc).lower()
                if terms and not any(t in hay for t in terms):
                    continue
                # WWR title format is usually "Company: Role at Location" or "Company: Role"
                company = ""
                job_title = title
                if ": " in title:
                    parts = title.split(": ", 1)
                    company = parts[0].strip()
                    job_title = parts[1].strip() if len(parts) > 1 else title
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title=job_title,
                    url=link,
                    snippet=desc[:250] if desc else "",
                    source_name=company or "We Work Remotely",
                    published_date=pub_date or None,
                    raw_json={"title": title, "link": link, "description": desc},
                    confidence=1.0,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("WeWorkRemotely RSS failed: %s", e)
        return results


weworkremotely_provider = WeWorkRemotelyProvider()
