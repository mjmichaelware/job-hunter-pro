"""Hacker News "Who is Hiring" — via Algolia HN Search API. Keyless.

Searches the monthly "Ask HN: Who is Hiring?" threads for job leads.
API docs: https://hn.algolia.com/api/v1/search (no key required).
"""
import logging
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

# The known parent story IDs for recent "Who is Hiring?" threads.
# Algolia search with restrictSearchableAttributes handles text filtering well,
# but we also accept HN story-level search via the tags filter.
_HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"


class HnHiringProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="hn_hiring",
            label="Hacker News Who is Hiring",
            type=ProviderType.SEARCH,
            description="Keyless search of HN 'Who is Hiring?' threads via Algolia.",
            requires_api_key=False,
            budget_class="free",
        )

    def is_available(self) -> bool:
        return True

    def search(self, query: str) -> List[SearchResult]:
        results: List[SearchResult] = []
        try:
            # Search HN comments tagged as job posts in Ask HN hiring threads.
            resp = http_session.get(
                _HN_SEARCH_URL,
                params={
                    "query": query,
                    "tags": "comment,ask_hn",
                    "hitsPerPage": 50,
                },
                timeout=12,
            )
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for hit in (resp.json().get("hits", []) or []):
                text = hit.get("comment_text") or hit.get("story_text") or ""
                # Only include hits that look like job listings (contain hiring signals).
                text_lower = text.lower()
                if not any(kw in text_lower for kw in ("hiring", "|", "salary", "remote", "onsite", "full-time")):
                    continue
                story_id = hit.get("objectID", "")
                url = "https://news.ycombinator.com/item?id=%s" % story_id if story_id else "https://news.ycombinator.com/jobs"
                author = hit.get("author", "")
                # Use first 200 chars of comment as snippet.
                snippet = text[:200].strip() if text else ""
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title="HN Hiring: %s" % (author or "Anonymous"),
                    url=url,
                    snippet=snippet,
                    source_name="Hacker News Who is Hiring",
                    published_date=hit.get("created_at"),
                    raw_json=hit,
                    confidence=0.7,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("HN Hiring search failed: %s", e)
        return results


hn_hiring_provider = HnHiringProvider()
