import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class BaseRepository:
    """Base repository providing standard CRUD operations with local fallback."""
    
    def __init__(self, collection_name: str, db=None):
        self.collection_name = collection_name
        self.db = db
        self._local_storage: Dict[str, Dict[str, Any]] = {}

    @property
    def collection(self):
        if not self.db:
            from store.firestore_client import get_db
            try:
                self.db = get_db()
            except Exception as e:
                logger.warning(f"Firestore unavailable for {self.collection_name}: {e}")
                return None
        return self.db.collection(self.collection_name)
    
    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        col = self.collection
        if col:
            try:
                doc = col.document(doc_id).get()
                return doc.to_dict() if doc.exists else None
            except Exception as e:
                logger.error(f"Firestore get failed for {self.collection_name}/{doc_id}: {e}")
        return self._local_storage.get(doc_id)

    def save(self, doc_id: str, data: Dict[str, Any]) -> None:
        self._local_storage[doc_id] = data
        col = self.collection
        if col:
            try:
                col.document(doc_id).set(data)
            except Exception as e:
                logger.error(f"Firestore save failed for {self.collection_name}/{doc_id}: {e}")

    def update(self, doc_id: str, data: Dict[str, Any]) -> None:
        if doc_id in self._local_storage:
            self._local_storage[doc_id].update(data)
        col = self.collection
        if col:
            try:
                col.document(doc_id).update(data)
            except Exception as e:
                logger.error(f"Firestore update failed for {self.collection_name}/{doc_id}: {e}")

    def delete(self, doc_id: str) -> None:
        self._local_storage.pop(doc_id, None)
        col = self.collection
        if col:
            try:
                col.document(doc_id).delete()
            except Exception as e:
                logger.error(f"Firestore delete failed for {self.collection_name}/{doc_id}: {e}")

    def get_all(self) -> List[Dict[str, Any]]:
        """Returns all documents in the collection, falling back to local if needed."""
        col = self.collection
        if col:
            try:
                docs = col.stream()
                return [doc.to_dict() for doc in docs]
            except Exception as e:
                logger.error(f"Firestore stream failed for {self.collection_name}: {e}")
        return list(self._local_storage.values())
