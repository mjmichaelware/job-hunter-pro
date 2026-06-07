import requests
from functools import lru_cache
from core.config import get_config
from core.errors import PlacesError

config = get_config()
API_KEY = config.GOOGLE_MAPS_API_KEY

@lru_cache(maxsize=128)
def places_text_search(query, location_bias=None):
    """Search for a place using Google Places Text Search."""
    if not API_KEY:
        raise PlacesError("Google Maps API key is not configured.")

    params = {
        'query': query,
        'key': API_KEY,
    }
    if location_bias:
        # e.g. "circle:radius@lat,lng"
        params['locationBias'] = location_bias

    try:
        response = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json', params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data['status'] not in ['OK', 'ZERO_RESULTS']:
            raise PlacesError(f"Places Text Search failed for query '{query}'. Status: {data['status']}")

        return data.get('results', [])
    except requests.exceptions.RequestException as e:
        raise PlacesError(f"HTTP error during places text search: {e}")
