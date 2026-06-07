import requests
from functools import lru_cache
from core.config import get_config
from core.errors import DistanceMatrixError

config = get_config()
API_KEY = config.GOOGLE_MAPS_API_KEY

@lru_cache(maxsize=256)
def get_distance_matrix(origins, destinations, mode='transit'):
    """Get travel distance and time using Google Distance Matrix API."""
    if not API_KEY:
        raise DistanceMatrixError("Google Maps API key is not configured.")

    # The API expects origins and destinations as pipe-separated strings.
    # The input to this function is expected to be a list of strings.
    origin_str = "|".join(origins)
    dest_str = "|".join(destinations)

    params = {
        'origins': origin_str,
        'destinations': dest_str,
        'key': API_KEY,
        'mode': mode,
    }

    try:
        response = requests.get('https://maps.googleapis.com/maps/api/distancematrix/json', params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['status'] != 'OK':
            # It can return OK but have non-OK status for elements.
            # A robust implementation would check element statuses.
            # For now, we check the top-level status.
            raise DistanceMatrixError(f"Distance Matrix failed with status: {data['status']}. Error message: {data.get('error_message', 'N/A')}")

        return data
    except requests.exceptions.RequestException as e:
        raise DistanceMatrixError(f"HTTP error during distance matrix fetch: {e}")
