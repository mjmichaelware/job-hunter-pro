"""Local-geography gate for discovery (origin: 28 E Bryan Ave, SLC, UT 84115).

Rule (explicit user request):
  * When a job has a computed ``radius_miles`` (Google Places / Haversine), it
    is kept only if it is within ``MAX_RADIUS_MILES`` (default 5).
  * When a job has NO exact address / no radius, it is kept only when the
    location text says Salt Lake City / South Salt Lake City (any "salt lake"
    or "slc" token). Bare street addresses (e.g. "123 Main St") are also kept
    because they may be local and cannot be proven otherwise.
  * Everything provably elsewhere (Berlin, Paris, New York, Provo, "Remote",
    blank, …) is excluded.

No role/industry/score restrictions are applied here — locality is the only
restriction.
"""

from __future__ import annotations

import os
import re

# Keep-list tokens for address-less jobs: Salt Lake City / South Salt Lake City.
_LOCAL_TOKENS = ("salt lake", "slc")

# Bare street-address detection: "123 Main St", "400 S 700 E", "Suite 200".
_STREET_SUFFIX = (
    r"(?:st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|way|ct|court|"
    r"ln|lane|pkwy|parkway|hwy|highway|cir|circle|pl|place|ter|terrace|"
    r"suite|ste|unit|#)"
)
_STREET_ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+[nesw]?\s*[a-z0-9.' -]{2,40}\b" + _STREET_SUFFIX + r"\b",
    re.I,
)
# Salt Lake grid-style address: "400 S 700 E", "2100 S State St".
_GRID_ADDRESS_RE = re.compile(r"\b\d{1,6}\s+[nesw]\s+\d{1,6}\s+[nesw]\b", re.I)

_NON_LOCAL_COUNTRIES = (
    "germany", "france", "united kingdom", "england", "scotland", "wales",
    "ireland", "canada", "mexico", "spain", "italy", "netherlands", "belgium",
    "switzerland", "austria", "poland", "portugal", "sweden", "norway",
    "denmark", "finland", "iceland", "luxembourg", "czech republic", "czechia",
    "slovakia", "slovenia", "hungary", "romania", "bulgaria", "croatia",
    "serbia", "ukraine", "russia", "greece", "turkey", "india", "pakistan",
    "bangladesh", "philippines", "indonesia", "malaysia", "singapore",
    "thailand", "vietnam", "japan", "china", "hong kong", "taiwan", "korea",
    "south korea", "australia", "new zealand", "brazil", "argentina", "chile",
    "colombia", "peru", "israel", "egypt", "nigeria", "kenya", "ghana",
    "south africa", "morocco", "united arab emirates", "saudi arabia", "qatar",
)

_NON_LOCAL_CITIES = (
    "berlin", "munich", "hamburg", "frankfurt", "cologne", "stuttgart",
    "paris", "lyon", "london", "manchester", "birmingham", "edinburgh",
    "dublin", "amsterdam", "rotterdam", "utrecht", "barcelona", "madrid",
    "lisbon", "porto", "rome", "milan", "turin", "zurich", "geneva",
    "vienna", "prague", "warsaw", "krakow", "budapest", "bucharest", "sofia",
    "athens", "stockholm", "oslo", "copenhagen", "helsinki", "brussels",
    "toronto", "vancouver", "montreal", "ottawa", "calgary", "mexico city",
    "guadalajara", "monterrey", "sao paulo", "rio de janeiro",
    "buenos aires", "santiago", "lima", "bogota", "bangalore", "bengaluru",
    "hyderabad", "mumbai", "pune", "chennai", "delhi", "new delhi", "noida",
    "gurgaon", "manila", "cebu", "jakarta", "bangkok", "hanoi", "ho chi minh",
    "kuala lumpur", "tokyo", "osaka", "seoul", "taipei", "shanghai",
    "beijing", "shenzhen", "sydney", "melbourne", "brisbane", "auckland",
    "wellington", "cape town", "johannesburg", "nairobi", "lagos", "cairo",
    "tel aviv", "dubai", "abu dhabi", "istanbul", "kyiv", "lviv",
    "new york", "brooklyn", "los angeles", "san francisco", "chicago",
    "boston", "seattle", "austin", "dallas", "houston", "denver", "phoenix",
    "atlanta", "miami", "philadelphia", "portland", "san diego", "san jose",
    "minneapolis", "detroit", "nashville", "charlotte", "raleigh",
    "las vegas", "boise", "provo", "orem", "logan", "st. george",
    "salt lake city, ut",  # never hit: kept earlier via _LOCAL_TOKENS
)

_NON_LOCAL_REGIONS = (
    "europe", "emea", "european union", "apac", "asia", "africa",
    "latin america", "south america", "middle east", "caribbean",
)

_OTHER_US_STATE_NAMES = (
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming",
)

# Unambiguous 2-letter state codes (excludes in/or/me/de/la/ma/md/ok/ar/co/hi).
_OTHER_STATE_ABBRS = (
    "ny", "ca", "tx", "wa", "fl", "il", "oh", "ga", "nc", "sc", "az", "nm",
    "nv", "id", "mt", "wy", "nd", "sd", "ne", "ks", "mn", "ia", "mo", "mi",
    "wi", "ky", "tn", "pa", "nj", "ct", "ri", "vt", "nh", "ak", "al", "ms",
    "wv", "va",
)

_STATE_ABBR_RE = re.compile(
    r"(?<![a-z])(" + "|".join(_OTHER_STATE_ABBRS) + r")(?![a-z])"
)


def local_gate_enabled() -> bool:
    """LOCAL_LOCATION_GATE=0 disables the whole locality gate."""
    return os.environ.get("LOCAL_LOCATION_GATE", "1").strip().lower() not in {
        "0", "false", "no", "off",
    }


def location_is_local(location: str) -> bool:
    """True when an address-less location is acceptable.

    Accept: Salt Lake City / South Salt Lake City text, "slc", or a bare
    street address. Reject: blank, remote/generic, foreign, other US states,
    other cities.
    """
    loc = re.sub(r"\s+", " ", str(location or "")).strip().lower()
    if not loc:
        return False

    if any(token in loc for token in _LOCAL_TOKENS):
        return True
    if re.search(r"(?<![a-z])slc(?![a-z])", loc):
        return True

    # A bare street address cannot be proven non-local; keep it.
    if _STREET_ADDRESS_RE.search(loc) or _GRID_ADDRESS_RE.search(loc):
        return True

    if any(country in loc for country in _NON_LOCAL_COUNTRIES):
        return False
    if any(
        re.search(r"(?<![a-z])" + re.escape(city) + r"(?![a-z])", loc)
        for city in _NON_LOCAL_CITIES
    ):
        return False
    if any(
        re.search(r"(?<![a-z])" + re.escape(region) + r"(?![a-z])", loc)
        for region in _NON_LOCAL_REGIONS
    ):
        return False
    if any(state in loc for state in _OTHER_US_STATE_NAMES):
        return False
    if _STATE_ABBR_RE.search(loc):
        return False

    return False


def job_within_local_radius(job: dict, max_radius_miles) -> bool:
    """True when the job is inside the 84115 radius (or cannot be proven outside)."""
    try:
        limit = float(max_radius_miles)
    except (TypeError, ValueError):
        return True
    if limit <= 0:
        return True

    for key in ("radius_miles", "distance_miles"):
        radius = job.get(key)
        if radius is not None:
            try:
                return float(radius) <= limit
            except (TypeError, ValueError):
                continue

    location = (
        job.get("resolved_address")
        or job.get("location")
        or job.get("listing_location")
        or ""
    )
    return location_is_local(location)
