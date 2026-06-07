import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
from store.repository import BaseRepository

logger = logging.getLogger(__name__)

class CacheRepository(BaseRepository):
    def __init__(self, db=None):
        super().__init__("cache", db)
        self._local_cache = {} # In-memory fallback

    def generate_key(self, provider: str, query: str, industry: str) -> str:
        """Generates a deterministic SHA-256 key for cache lookup."""
        raw = f"{provider.lower()}|{query.lower()}|{industry.lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_cached_results(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieves results from cache, failing over to local memory."""
        try:
            # Try Firestore first
            doc = self.get(key)
            if doc:
                return doc.get("results")
        except Exception as e:
            logger.error(f"Firestore cache get failed: {e}. Falling back to memory.")
        
        # Local fallback
        return self._local_cache.get(key)

    def set_cached_results(self, key: str, data: Dict[str, Any]) -> None:
        """Stores results in cache and local memory."""
        # Always store locally
        self._local_cache[key] = data.get("results")
        
        try:
            # Try Firestore
            self.save(key, data)
        except Exception as e:
            logger.error(f"Firestore cache set failed: {e}.")
