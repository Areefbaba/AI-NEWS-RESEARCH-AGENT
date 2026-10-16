"""Repository pattern for articles, feed cache, source health, and briefings."""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from app.schemas.article import NormalizedArticle
from app.schemas.briefing import NewsBriefing
from app.schemas.source import SourceHealth
from app.storage.database import Database

logger = logging.getLogger(__name__)


class ArticleRepository:
    """CRUD operations for normalized articles, feed cache, and briefings."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    def save_article(self, article: NormalizedArticle) -> bool:
        """Upsert a normalized article into SQLite."""
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO articles (
                    id, canonical_url, title, source_name, source_domain,
                    category, subcategory, published_at, retrieved_at,
                    short_description, extracted_content, content_fingerprint,
                    importance_score, verification_status, serialized_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(canonical_url) DO UPDATE SET
                    title = excluded.title,
                    importance_score = excluded.importance_score,
                    verification_status = excluded.verification_status,
                    serialized_json = excluded.serialized_json;
                """, (
                    article.id,
                    article.canonical_url,
                    article.title,
                    article.source_name,
                    article.source_domain,
                    article.category,
                    article.subcategory,
                    article.published_at.isoformat() if article.published_at else None,
                    article.retrieved_at.isoformat(),
                    article.short_description,
                    article.extracted_content_or_excerpt,
                    article.content_fingerprint,
                    article.importance_score,
                    article.verification_status,
                    article.model_dump_json()
                ))
                return True
        except Exception as e:
            logger.error("Failed to save article %s: %s", article.canonical_url, e)
            return False

    def get_articles_by_category(self, category: str, limit: int = 50) -> List[NormalizedArticle]:
        """Fetch cached articles by category."""
        articles = []
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT serialized_json FROM articles
                WHERE category = ?
                ORDER BY published_at DESC, importance_score DESC
                LIMIT ?;
                """, (category, limit))
                for row in cursor.fetchall():
                    articles.append(NormalizedArticle.model_validate_json(row["serialized_json"]))
        except Exception as e:
            logger.error("Failed to fetch articles for category %s: %s", category, e)
        return articles

    def article_exists(self, canonical_url: str) -> bool:
        """Check if an article exists by canonical URL."""
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM articles WHERE canonical_url = ? LIMIT 1;", (canonical_url,))
            return cursor.fetchone() is not None

    def fingerprint_exists(self, fingerprint: str) -> bool:
        """Check if content fingerprint already exists."""
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM articles WHERE content_fingerprint = ? LIMIT 1;", (fingerprint,))
            return cursor.fetchone() is not None

    # Feed Cache Operations
    def get_feed_cache(self, url: str) -> Optional[str]:
        """Retrieve unexpired cached feed content."""
        try:
            now_str = datetime.now(timezone.utc).isoformat()
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT content FROM feed_cache
                WHERE url = ? AND expires_at > ?;
                """, (url, now_str))
                row = cursor.fetchone()
                if row:
                    return row["content"]
        except Exception as e:
            logger.warning("Error reading feed cache for %s: %s", url, e)
        return None

    def set_feed_cache(self, url: str, content: str, ttl_hours: int = 2) -> None:
        """Cache feed response with expiration TTL."""
        try:
            now = datetime.now(timezone.utc)
            expires_at = (now + timedelta(hours=ttl_hours)).isoformat()
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO feed_cache (url, content, fetched_at, expires_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    content = excluded.content,
                    fetched_at = excluded.fetched_at,
                    expires_at = excluded.expires_at;
                """, (url, content, now.isoformat(), expires_at))
        except Exception as e:
            logger.warning("Error writing feed cache for %s: %s", url, e)

    # Source Health Telemetry
    def update_source_health(self, health: SourceHealth) -> None:
        """Record health check results for a source."""
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO source_health (
                    source_id, name, status, last_attempt, last_success, error_message, latency_ms, items_fetched
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    status = excluded.status,
                    last_attempt = excluded.last_attempt,
                    last_success = excluded.last_success,
                    error_message = excluded.error_message,
                    latency_ms = excluded.latency_ms,
                    items_fetched = excluded.items_fetched;
                """, (
                    health.source_id,
                    health.name,
                    health.status,
                    health.last_attempt.isoformat() if health.last_attempt else None,
                    health.last_success.isoformat() if health.last_success else None,
                    health.error_message,
                    health.latency_ms,
                    health.items_fetched
                ))
        except Exception as e:
            logger.warning("Failed to record source health for %s: %s", health.source_id, e)

    def get_all_source_health(self) -> Dict[str, str]:
        """Return mapping of source_id -> status."""
        health_map = {}
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT source_id, status FROM source_health;")
                for row in cursor.fetchall():
                    health_map[row["source_id"]] = row["status"]
        except Exception as e:
            logger.warning("Failed to get all source health: %s", e)
        return health_map

    # Briefings Cache Operations
    def get_cached_briefing(self, domain: str, category_filter: Optional[str] = None) -> Optional[NewsBriefing]:
        """Fetch unexpired generated briefing."""
        try:
            cache_key = f"{domain}:{category_filter or 'all'}"
            now_str = datetime.now(timezone.utc).isoformat()
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT briefing_json FROM briefings_cache
                WHERE cache_key = ? AND expires_at > ?;
                """, (cache_key, now_str))
                row = cursor.fetchone()
                if row:
                    briefing = NewsBriefing.model_validate_json(row["briefing_json"])
                    briefing.is_cached = True
                    return briefing
        except Exception as e:
            logger.warning("Error fetching briefing cache for %s: %s", domain, e)
        return None

    def cache_briefing(self, briefing: NewsBriefing, ttl_hours: int = 1) -> None:
        """Cache generated briefing with TTL."""
        try:
            cache_key = f"{briefing.domain}:{briefing.category_filter or 'all'}"
            now = datetime.now(timezone.utc)
            expires_at = (now + timedelta(hours=ttl_hours)).isoformat()
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO briefings_cache (cache_key, domain, category_filter, briefing_json, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    briefing_json = excluded.briefing_json,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at;
                """, (
                    cache_key,
                    briefing.domain,
                    briefing.category_filter,
                    briefing.model_dump_json(),
                    now.isoformat(),
                    expires_at
                ))
        except Exception as e:
            logger.warning("Error saving briefing cache for %s: %s", briefing.domain, e)
