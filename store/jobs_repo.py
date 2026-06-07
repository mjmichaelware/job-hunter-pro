from typing import Dict, Any, List
from store.repository import BaseRepository

class JobsRepository(BaseRepository):
    def __init__(self, db=None):
        super().__init__("jobs", db)
        
    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        docs = self.collection.where("status", "==", status).stream()
        return [doc.to_dict() for doc in docs]
