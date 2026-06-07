import requests
import time
from core.config import get_config
from core.errors import PlacesError

config = get_config()
API_KEY = config.GOOGLE_MAPS_API_KEY

def places_nearby_search(latitude, longitude, radius_meters, keyword=None, place_type=None):
    """Search for nearby places using Google Places Nearby Search."""
    if not API_KEY:
        raise PlacesError("Google Maps API key is not configured.")

    params = {
        'location': f"{latitude},{longitude}",
        'radius': radius_meters,
        'key': API_KEY,
    }
    if keyword:
        params['keyword'] = keyword
    if place_type:
        params['type'] = place_type

    results = []
    
    try:
        while True:
            response = requests.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json', params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['status'] not in ['OK', 'ZERO_RESULTS']:
                raise PlacesError(f"Places Nearby Search failed. Status: {data['status']}")

            results.extend(data.get('results', []))

            next_page_token = data.get('next_page_token')
            if not next_page_token:
                break
            
            # Remove all params except pagetoken and key for subsequent requests
            params = {
                'pagetoken': next_page_token,
                'key': API_KEY
            }
            # Per Google's docs, there's a required delay before the next page token becomes valid.
            time.sleep(2)
            
    except requests.exceptions.RequestException as e:
        raise PlacesError(f"HTTP error during places nearby search: {e}")

    return results
