import os
from functools import lru_cache

class Config:
    """
    Configuration class for the application.
    Reads all settings from environment variables.
    Secrets are not hardcoded but read at runtime.
    """
    # Core Infrastructure
    PROJECT_ID = os.environ.get("PROJECT_ID", "ai-job-agent-498702")
    REGION = os.environ.get("REGION", "us-central1")
    BATCH_BUCKET = os.environ.get("BATCH_BUCKET", "")

    # Geo/Maps Settings
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    ORIGIN_ADDRESS = os.environ.get("ORIGIN_ADDRESS", "28 E Bryan Ave, Salt Lake City, UT 84115")
    JOB_LOCATION_DEFAULT = os.environ.get("JOB_LOCATION_DEFAULT", "84115")
    MAX_TRANSIT_SECONDS = int(os.environ.get("MAX_TRANSIT_SECONDS", 35 * 60))
    MAX_RADIUS_MILES = float(os.environ.get("MAX_RADIUS_MILES", 2.5))

    # Provider Keys (Secrets)
    SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
    ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
    ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
    USAJOBS_API_KEY = os.environ.get("USAJOBS_API_KEY", "")
    USAJOBS_EMAIL = os.environ.get("USAJOBS_EMAIL", "")
    JOOBLE_API_KEY = os.environ.get("JOOBLE_API_KEY", "")
    CAREERJET_AFFID = os.environ.get("CAREERJET_AFFID", "")

    # Budget & Quota Guards
    SERPAPI_BUDGET_MODE = os.environ.get("SERPAPI_BUDGET_MODE", "1") == "1"
    SERPAPI_MIN_SEARCHES_LEFT = int(os.environ.get("SERPAPI_MIN_SEARCHES_LEFT", 40))
    MAX_SERP_QUERIES_PER_RUN = int(os.environ.get("MAX_SERP_QUERIES_PER_RUN", 4))
    MAX_RAW_JOBS_PER_RUN = int(os.environ.get("MAX_RAW_JOBS_PER_RUN", 35))
    MAX_AI_CALLS_PER_RUN = int(os.environ.get("MAX_AI_CALLS_PER_RUN", 8))

    # Ingestion Security
    INGEST_TOKEN_LEGACY = os.environ.get("INGEST_TOKEN_LEGACY", "") # To be deprecated
    SCHEDULER_SA_EMAIL = f"job-hunter-scheduler@{PROJECT_ID}.iam.gserviceaccount.com"

    # HTTP Client Settings
    REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", 12.0))

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

@lru_cache()
def get_config():
    """Returns a cached instance of the Config class."""
    return Config()
