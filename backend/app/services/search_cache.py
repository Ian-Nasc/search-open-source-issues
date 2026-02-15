"""SQLite-based search cache with 48h TTL.

Caches search results to avoid repeated LLM/embedding calls for common queries.
"""
import hashlib
import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 48
CACHE_DB = Path(__file__).parent.parent.parent / "data" / "search_cache.db"


class SearchCache:
    _local = threading.local()

    def __init__(self):
        CACHE_DB.parent.mkdir(exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(str(CACHE_DB), check_same_thread=False)
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS search_cache (
                cache_key TEXT PRIMARY KEY,
                results TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON search_cache(created_at)
        """)
        conn.commit()

    def _make_key(self, query: str, filters: dict) -> str:
        """Create a deterministic cache key from query + filters."""
        data = json.dumps({"q": query.lower().strip(), **filters}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def get(self, query: str, filters: dict) -> list[int] | None:
        """Get cached issue IDs for a query, or None if not cached/expired."""
        key = self._make_key(query, filters)
        conn = self._get_conn()

        cur = conn.execute(
            "SELECT results, created_at FROM search_cache WHERE cache_key = ?",
            (key,)
        )
        row = cur.fetchone()

        if not row:
            return None

        created = datetime.fromisoformat(row[1])
        if datetime.utcnow() - created > timedelta(hours=CACHE_TTL_HOURS):
            conn.execute("DELETE FROM search_cache WHERE cache_key = ?", (key,))
            conn.commit()
            logger.debug(f"Cache expired for query: {query[:50]}")
            return None

        logger.debug(f"Cache hit for query: {query[:50]}")
        return json.loads(row[0])

    def set(self, query: str, filters: dict, issue_ids: list[int]):
        """Cache issue IDs for a query."""
        key = self._make_key(query, filters)
        conn = self._get_conn()

        conn.execute(
            "INSERT OR REPLACE INTO search_cache (cache_key, results, created_at) VALUES (?, ?, ?)",
            (key, json.dumps(issue_ids), datetime.utcnow().isoformat())
        )
        conn.commit()
        logger.debug(f"Cached {len(issue_ids)} results for query: {query[:50]}")

    def cleanup_expired(self):
        """Remove all expired entries."""
        conn = self._get_conn()
        cutoff = (datetime.utcnow() - timedelta(hours=CACHE_TTL_HOURS)).isoformat()
        result = conn.execute(
            "DELETE FROM search_cache WHERE created_at < ?",
            (cutoff,)
        )
        conn.commit()
        logger.info(f"Cleaned up {result.rowcount} expired cache entries")


search_cache = SearchCache()
