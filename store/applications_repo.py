import logging
from typing import List, Dict, Any, Optional
from store.repository import BaseRepository

logger = logging.getLogger(__name__)

class ApplicationsRepository(BaseRepository):
    def __init__(self, db=None):
        super().__init__("applications", db)
        self._local_storage = {} # In-memory fallback

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieves all applications."""
        try:
            docs = self.collection.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Firestore applications stream failed: {e}. Using local.")
            return list(self._local_storage.values())

    def get_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single application by job_id."""
        try:
            return self.get(job_id)
        except Exception as e:
            logger.error(f"Firestore applications get failed: {e}. Using local.")
            return self._local_storage.get(job_id)

    def save_application(self, job_id: str, data: Dict[str, Any]) -> None:
        """Saves or updates an application."""
        self._local_storage[job_id] = data
        try:
            self.save(job_id, data)
        except Exception as e:
            logger.error(f"Firestore applications save failed: {e}.")
