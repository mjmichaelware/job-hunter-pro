"""OpenStreetMap Overpass — businesses within a radius of the origin as opportunity
LEADS (not job posts). Keyless. Default OFF: set ENABLE_OSM_OVERPASS=1 to include.
This powers the broad 50-mile opportunity sweep from 84115.
"""
import logging
import os
from typing import List

from models import SearchResult
from core import http_session
from core.errors import ProviderHardFailure
from ..base import ProviderMetadata, ProviderType, SearchProvider, check_hard_failure

logger = logging.getLogger(__name__)

ORIGIN_LAT = float(os.environ.get("ORIGIN_LAT", "40.7106"))
ORIGIN_LNG = float(os.environ.get("ORIGIN_LNG", "-111.8867"))
# radius in meters (default ~10 mi; 50 mi = 80467). Keep modest to bound result size.
OSM_RADIUS_M = int(os.environ.get("OSM_RADIUS_M", "16093"))


class OsmOverpassProvider(SearchProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            key="osm_overpass",
            label="OSM Overpass (nearby businesses)",
            type=ProviderType.SEARCH,
            description="Named businesses within radius of origin as opportunity leads.",
            requires_api_key=False,
        )

    def is_available(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        # ON by default; opt-out by setting DISABLE_OSM_OVERPASS=1.
        return "Disabled via DISABLE_OSM_OVERPASS env flag." if os.environ.get("DISABLE_OSM_OVERPASS") else ""

    def search(self, query: str) -> List[SearchResult]:
        # Overpass QL: named shops/offices/amenities within the radius of origin.
        q = ('[out:json][timeout:20];('
             'node(around:%d,%f,%f)[name][shop];'
             'node(around:%d,%f,%f)[name][office];'
             'node(around:%d,%f,%f)[name][amenity];'
             ');out 60;') % (
            OSM_RADIUS_M, ORIGIN_LAT, ORIGIN_LNG,
            OSM_RADIUS_M, ORIGIN_LAT, ORIGIN_LNG,
            OSM_RADIUS_M, ORIGIN_LAT, ORIGIN_LNG,
        )
        terms = [w for w in query.lower().split() if len(w) > 3]
        results: List[SearchResult] = []
        try:
            resp = http_session.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=25)
            check_hard_failure(self.metadata.key, resp)
            resp.raise_for_status()
            for el in (resp.json().get("elements", []) or []):
                tags = el.get("tags", {}) or {}
                name = tags.get("name", "")
                if not name:
                    continue
                cat = tags.get("shop") or tags.get("office") or tags.get("amenity") or ""
                if terms and not any(t in (name + " " + cat).lower() for t in terms):
                    continue
                lat, lon = el.get("lat"), el.get("lon")
                results.append(SearchResult(
                    provider=self.metadata.key,
                    query=query,
                    title="Nearby business: %s" % name,
                    url="https://www.openstreetmap.org/node/%s" % el.get("id", ""),
                    snippet=cat,
                    source_name=name,
                    published_date=None,
                    raw_json={"tags": tags, "lat": lat, "lon": lon},
                    confidence=0.4,
                    cost_units=0.0,
                ))
        except ProviderHardFailure:
            raise
        except Exception as e:
            logger.error("OSM Overpass failed: %s", e)
        return results


osm_overpass_provider = OsmOverpassProvider()
