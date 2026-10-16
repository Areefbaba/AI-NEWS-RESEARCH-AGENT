"""SQLite database connection and schema management."""

import os
import sqlite3
import logging
from contextlib import contextmanager
from typing import Generator, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)


class Database:
    """SQLite Database manager with connection lifecycle and migrations."""

    def __init__(self, db_path: Optional[str] = None):
        settings = get_settings()
        self.db_path = db_path or settings.DATABASE_PATH
        self._mem_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
        else:
            self._ensure_dir()
        self.init_db()

    def _ensure_dir(self) -> None:
        """Ensure parent directory for database exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a managed SQLite connection that automatically commits and closes."""
        if self._mem_conn is not None:
            try:
                yield self._mem_conn
                self._mem_conn.commit()
            except Exception:
                self._mem_conn.rollback()
                raise
        else:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("PRAGMA foreign_keys = ON;")
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def init_db(self) -> None:
        """Create database tables if they do not exist."""
        with self.connection() as conn:
            cursor = conn.cursor()

            # Articles table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                canonical_url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_domain TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                published_at TEXT,
                retrieved_at TEXT NOT NULL,
                short_description TEXT,
                extracted_content TEXT,
                content_fingerprint TEXT NOT NULL,
                importance_score REAL DEFAULT 0.0,
                verification_status TEXT DEFAULT 'unconfirmed',
                serialized_json TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_fingerprint ON articles(content_fingerprint);
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);
            """)

            # Feed Cache table with TTL
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS feed_cache (
                url TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                etag TEXT,
                last_modified TEXT,
                fetched_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            """)

            # Source Health Telemetry
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_health (
                source_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                last_attempt TEXT,
                last_success TEXT,
                error_message TEXT,
                latency_ms REAL,
                items_fetched INTEGER DEFAULT 0
            );
            """)

            # Briefings Cache table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS briefings_cache (
                cache_key TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                category_filter TEXT,
                briefing_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            """)

            logger.info("Database initialized successfully at %s", self.db_path)
