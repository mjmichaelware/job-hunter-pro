from typing import Dict, Any, List
from store.repository import BaseRepository

class JobsRepository(BaseRepository):
    def __init__(self, db=None):
        super().__init__("jobs", db)
        
    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        all_docs = self.get_all()
        return [doc for doc in all_docs if doc.get("status") == status]
