from typing import Dict, Any, List
from store.repository import BaseRepository
from store.sqlite_repo import SQLiteJobsRepository as _SQLiteJobsRepo


class JobsRepository(BaseRepository):
    def __init__(self, db=None):
        super().__init__("jobs", db)
        self._sqlite = None

    @property
    def sqlite(self):
        if self._sqlite is None:
            from store.sqlite_repo import get_sqlite_jobs_repo
            self._sqlite = get_sqlite_jobs_repo()
        return self._sqlite

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        # Use SQLite local store if Firestore is unavailable
        all_docs = self.get_all()
        return [doc for doc in all_docs if doc.get("status") == status]
