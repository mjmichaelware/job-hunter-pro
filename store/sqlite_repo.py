"""SQLite-backed repositories as a local fallback to Firestore.

Usage:
    from store.sqlite_repo import SQLiteJobsRepository, SQLiteBatchesRepository

    jobs_repo = SQLiteJobsRepository()
    jobs_repo.save("job1", {"title": "Software Engineer", ...})
    jobs = jobs_repo.find_by_status("accepted")
"""
import hashlib
import json
import logging
import sqlite3
import threading
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SQLiteRepository:
    """Base repository using SQLite for local storage.

    Each instance uses a separate file keyed by collection_name.
    Thread-safe via a per-connection lock.
    """

    def __init__(self, collection_name: str, db_path: str = ":memory:"):
        self.collection_name = collection_name
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS `{self.collection_name}` (
                    doc_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _compute_doc_id(self, data: Dict[str, Any]) -> str:
        """Generate a deterministic doc_id from the data payload."""
        payload = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]

    def save(self, doc_id: str, data: Dict[str, Any]) -> None:
        """Save a document into the SQLite store."""
        with self._lock:
            conn = self._get_conn()
            try:
                doc_id = doc_id or self._compute_doc_id(data)
                conn.execute(
                    f"INSERT OR REPLACE INTO `{self.collection_name}` (doc_id, data, created_at) VALUES (?, ?, ?)",
                    (doc_id, json.dumps(data, default=str), self._utc_now_iso()),
                )
                conn.commit()
            except Exception as e:
                logger.error(f"SQLite save failed for {self.collection_name}/{doc_id}: {e}")
            finally:
                conn.close()

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by doc_id."""
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute(
                    f"SELECT data FROM `{self.collection_name}` WHERE doc_id = ?", (doc_id,)
                ).fetchone()
                if row:
                    return json.loads(row[0])
            except Exception as e:
                logger.error(f"SQLite get failed for {self.collection_name}/{doc_id}: {e}")
            finally:
                conn.close()
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all documents in the collection."""
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    f"SELECT data FROM `{self.collection_name}`"
                ).fetchall()
                return [json.loads(row[0]) for row in rows]
            except Exception as e:
                logger.error(f"SQLite get_all failed for {self.collection_name}: {e}")
            finally:
                conn.close()
        return []

    def update(self, doc_id: str, data: Dict[str, Any]) -> None:
        """Update a document (additive merge)."""
        with self._lock:
            conn = self._get_conn()
            try:
                # Ensure doc_id exists; if not, insert
                existing = self.get(doc_id)
                if existing is None:
                    data["_doc_id"] = doc_id
                    self.save(doc_id, data)
                else:
                    existing.update(data)
                    conn.execute(
                        f"UPDATE `{self.collection_name}` SET data = ?, created_at = ? "
                        f"WHERE doc_id = ?",
                        (json.dumps(existing, default=str), self._utc_now_iso(), doc_id),
                    )
                    conn.commit()
            except Exception as e:
                logger.error(f"SQLite update failed for {self.collection_name}/{doc_id}: {e}")
            finally:
                conn.close()

    def delete(self, doc_id: str) -> None:
        """Delete a document by doc_id."""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    f"DELETE FROM `{self.collection_name}` WHERE doc_id = ?",
                    (doc_id,),
                )
                conn.commit()
            except Exception as e:
                logger.error(f"SQLite delete failed for {self.collection_name}/{doc_id}: {e}")
            finally:
                conn.close()

    @staticmethod
    def _utc_now_iso() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class SQLiteJobsRepository(SQLiteRepository):
    """SQLite-backed jobs repository."""

    def __init__(self, db_path: str = ":memory:"):
        super().__init__("jobs", db_path)

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        all_docs = self.get_all()
        return [doc for doc in all_docs if doc.get("status") == status]


class SQLiteBatchesRepository(SQLiteRepository):
    """SQLite-backed batches repository."""

    def __init__(self, db_path: str = ":memory:"):
        super().__init__("batches", db_path)


class SQLiteCacheRepository(SQLiteRepository):
    """SQLite-backed cache repository with deterministic keys."""

    def __init__(self, db_path: str = ":memory:"):
        super().__init__("cache", db_path)

    def generate_key(self, provider: str, query: str, industry: str) -> str:
        """Generates a deterministic SHA-256 key for cache lookup."""
        raw = f"{provider.lower()}|{query.lower()}|{industry.lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_cached_results(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve results from cache."""
        doc = self.get(key)
        if doc:
            return doc.get("results")
        return None

    def set_cached_results(self, key: str, data: Dict[str, Any]) -> None:
        """Store results in cache."""
        self.save(key, {"results": data.get("results") if isinstance(data, dict) else data})


# One instance per distinct db_path (prevents a singleton from silently using
# a different db if it was created with a different path first).
_repos: Dict[tuple, Any] = {}


def get_sqlite_jobs_repo(db_path: str = ":memory:") -> SQLiteJobsRepository:
    key = ("jobs", db_path)
    if key not in _repos:
        _repos[key] = SQLiteJobsRepository(db_path)
    return _repos[key]


def get_sqlite_batches_repo(db_path: str = ":memory:") -> SQLiteBatchesRepository:
    key = ("batches", db_path)
    if key not in _repos:
        _repos[key] = SQLiteBatchesRepository(db_path)
    return _repos[key]


def get_sqlite_cache_repo(db_path: str = ":memory:") -> SQLiteCacheRepository:
    key = ("cache", db_path)
    if key not in _repos:
        _repos[key] = SQLiteCacheRepository(db_path)
    return _repos[key]