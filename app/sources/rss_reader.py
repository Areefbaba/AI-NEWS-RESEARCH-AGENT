"""Resilient RSS and Atom feed reader adapter with caching and health monitoring."""

import time
import logging
from datetime import datetime, timezone
from typing import List, Optional
import feedparser
import httpx

from app.config import get_settings
from app.schemas.article import RawArticle
from app.schemas.source import SourceConfig, SourceHealth
from app.sources.base import BaseSourceAdapter
from app.storage.repository import ArticleRepository

logger = logging.getLogger(__name__)


class RSSReaderAdapter(BaseSourceAdapter):
    """Fetches and parses RSS/Atom feeds with timeouts, health checks, and caching."""

    def __init__(self, repo: Optional[ArticleRepository] = None):
        super().__init__(repo)
        self.settings = get_settings()

    def fetch(self, config: SourceConfig) -> List[RawArticle]:
        """Fetch and parse feed entries safely."""
        start_time = time.time()
        articles: List[RawArticle] = []
        status = "healthy"
        error_msg: Optional[str] = None
        latency_ms: float = 0.0

        # Check local cache first
        cached_content = self.repo.get_feed_cache(config.url)
        content_to_parse = cached_content

        if not content_to_parse:
            try:
                headers = {
                    "User-Agent": self.settings.USER_AGENT,
                    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
                }
                with httpx.Client(
                    timeout=config.timeout_seconds,
                    follow_redirects=True,
                    headers=headers
                ) as client:
                    response = client.get(config.url)
                    latency_ms = (time.time() - start_time) * 1000

                    if response.status_code == 200:
                        content_to_parse = response.text
                        self.repo.set_feed_cache(config.url, content_to_parse, ttl_hours=self.settings.CACHE_TTL_HOURS)
                    else:
                        status = "degraded"
                        error_msg = f"HTTP {response.status_code}: {response.reason_phrase}"
                        logger.warning("Feed %s returned status %d", config.source_id, response.status_code)

            except httpx.TimeoutException as e:
                status = "failing"
                error_msg = f"Timeout after {config.timeout_seconds}s"
                logger.warning("Feed %s timed out: %s", config.source_id, e)
            except httpx.RequestError as e:
                status = "failing"
                error_msg = f"Request error: {str(e)}"
                logger.warning("Feed %s request error: %s", config.source_id, e)
            except Exception as e:
                status = "failing"
                error_msg = f"Unexpected error: {str(e)}"
                logger.exception("Feed %s encountered unexpected exception", config.source_id)

        # Parse content if available
        if content_to_parse:
            try:
                feed = feedparser.parse(content_to_parse)
                if feed.bozo and not feed.entries:
                    status = "degraded"
                    error_msg = f"Malformed XML: {getattr(feed, 'bozo_exception', 'unknown bozo')}"
                else:
                    for entry in feed.entries:
                        title = getattr(entry, "title", "").strip()
                        link = getattr(entry, "link", "").strip()
                        if not title or not link:
                            continue

                        # Extract summary / content
                        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                        content = ""
                        if hasattr(entry, "content") and entry.content:
                            content = entry.content[0].value
                        elif hasattr(entry, "summary_detail") and entry.summary_detail:
                            content = entry.summary_detail.value

                        author = getattr(entry, "author", None)
                        published = (
                            getattr(entry, "published", None) or
                            getattr(entry, "updated", None) or
                            getattr(entry, "created", None)
                        )

                        articles.append(RawArticle(
                            source_id=config.source_id,
                            source_name=config.name,
                            source_domain=config.domain,
                            url=link,
                            title=title,
                            summary_raw=summary,
                            content_raw=content or summary,
                            author=author,
                            published_raw=published,
                            retrieved_at=datetime.now(timezone.utc),
                            extra_metadata={
                                "feed_title": getattr(feed.feed, "title", ""),
                                "subcategories": ",".join(config.subcategories)
                            }
                        ))
            except Exception as e:
                status = "degraded"
                error_msg = f"Parsing failed: {str(e)}"
                logger.error("Failed to parse feed content for %s: %s", config.source_id, e)

        # Record source health
        health = SourceHealth(
            source_id=config.source_id,
            name=config.name,
            status=status,
            last_attempt=datetime.now(timezone.utc),
            last_success=datetime.now(timezone.utc) if status == "healthy" else None,
            error_message=error_msg,
            latency_ms=latency_ms if latency_ms > 0 else None,
            items_fetched=len(articles)
        )
        self.repo.update_source_health(health)

        return articles
