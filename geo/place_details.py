import requests
from functools import lru_cache
from core.config import get_config
from core.errors import PlacesError

config = get_config()
API_KEY = config.GOOGLE_MAPS_API_KEY

@lru_cache(maxsize=256)
def get_place_details(place_id, fields=None):
    """Get details for a specific place using Google Place Details API."""
    if not API_KEY:
        raise PlacesError("Google Maps API key is not configured.")

    default_fields = [
        "place_id", "name", "formatted_address", "geometry", "rating",
        "user_ratings_total", "business_status", "website", "reviews",
        "serves_beer", "serves_wine", "price_level", "editorial_summary"
    ]

    params = {
        'place_id': place_id,
        'key': API_KEY,
        'fields': ",".join(fields if fields else default_fields)
    }

    try:
        response = requests.get('https://maps.googleapis.com/maps/api/place/details/json', params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data['status'] != 'OK':
            raise PlacesError(f"Place Details failed for place_id '{place_id}'. Status: {data['status']}")

        return data.get('result', {})
    except requests.exceptions.RequestException as e:
        raise PlacesError(f"HTTP error during place details fetch: {e}")
