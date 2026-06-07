import requests
from functools import lru_cache
from core.config import get_config
from core.errors import GeocodingError

config = get_config()
API_KEY = config.GOOGLE_MAPS_API_KEY

@lru_cache(maxsize=128)
def geocode_address(address):
    """Geocode an address to lat/lng using Google Geocoding API."""
    if not API_KEY:
        raise GeocodingError("Google Maps API key is not configured.")

    params = {
        'address': address,
        'key': API_KEY
    }
    # Using a shared session is better, but for simplicity here, we use requests directly.
    # In a real app, inject a configured session from core.http.
    try:
        response = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data['status'] != 'OK' or not data.get('results'):
            raise GeocodingError(f"Geocoding failed for address '{address}'. Status: {data['status']}")

        location = data['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    except requests.exceptions.RequestException as e:
        raise GeocodingError(f"HTTP error during geocoding: {e}")

