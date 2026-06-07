from typing import Dict, Any, Optional

class BaseRepository:
    """Base repository providing standard CRUD operations."""
    
    def __init__(self, collection_name: str, db=None):
        self.collection_name = collection_name
        self.db = db

    @property
    def collection(self):
        if not self.db:
            from store.firestore_client import get_db
            self.db = get_db()
        return self.db.collection(self.collection_name)
    
    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.document(doc_id).get()
        return doc.to_dict() if doc.exists else None

    def save(self, doc_id: str, data: Dict[str, Any]) -> None:
        self.collection.document(doc_id).set(data)

    def update(self, doc_id: str, data: Dict[str, Any]) -> None:
        self.collection.document(doc_id).update(data)

    def delete(self, doc_id: str) -> None:
        self.collection.document(doc_id).delete()
