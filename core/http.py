import requests
from .config import Config

def get_http_session() -> requests.Session:
    """
    Returns a configured requests.Session instance for making HTTP calls.
    This can be expanded with default headers, retry logic, etc.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": f"JobHunterPro/1.0 (Project: {Config.PROJECT_ID})",
    })
    return session

# A global session instance to be used by various modules
http_session = get_http_session()
