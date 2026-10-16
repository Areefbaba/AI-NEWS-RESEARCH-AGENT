"""Unit tests for SQLite storage and repository."""

import os
import tempfile
from datetime import datetime, timezone
import pytest
from app.storage.database import Database
from app.storage.repository import ArticleRepository
from app.schemas.article import NormalizedArticle
from app.schemas.source import SourceHealth
from app.schemas.briefing import NewsBriefing, NewsCard


@pytest.fixture
def temp_repo():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    db = Database(db_path=db_path)
    repo = ArticleRepository(db=db)
    yield repo
    # On Windows, allow garbage collection before removing test db
    import gc, shutil
    gc.collect()
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


def test_article_save_and_retrieve(temp_repo):
    now = datetime.now(timezone.utc)
    article = NormalizedArticle(
        id="art_1",
        title="India test series triumph in decisive fashion",
        canonical_url="https://cricinfo.com/series/test-1",
        source_name="ESPNcricinfo",
        source_domain="espncricinfo.com",
        published_at=now,
        retrieved_at=now,
        category="cricket",
        subcategory="test_cricket",
        short_description="Historic 3-0 clean sweep completed.",
        extracted_content_or_excerpt="Full article body content.",
        content_fingerprint="fp123456",
        importance_score=0.92,
        verification_status="verified"
    )

    success = temp_repo.save_article(article)
    assert success is True
    assert temp_repo.article_exists(article.canonical_url) is True
    assert temp_repo.fingerprint_exists(article.content_fingerprint) is True

    articles = temp_repo.get_articles_by_category("cricket")
    assert len(articles) == 1
    assert articles[0].id == "art_1"
    assert articles[0].importance_score == 0.92


def test_feed_cache_ttl(temp_repo):
    url = "https://example.com/feed.xml"
    content = "<rss><channel><title>Test</title></channel></rss>"

    temp_repo.set_feed_cache(url, content, ttl_hours=2)
    cached = temp_repo.get_feed_cache(url)
    assert cached == content

    # Non-existent
    assert temp_repo.get_feed_cache("https://example.com/nonexistent") is None


def test_source_health_update(temp_repo):
    health = SourceHealth(
        source_id="bbc_world",
        name="BBC World",
        status="healthy",
        last_attempt=datetime.now(timezone.utc),
        last_success=datetime.now(timezone.utc),
        latency_ms=120.5,
        items_fetched=15
    )
    temp_repo.update_source_health(health)
    health_map = temp_repo.get_all_source_health()
    assert "bbc_world" in health_map
    assert health_map["bbc_world"] == "healthy"


def test_briefing_cache(temp_repo):
    card = NewsCard(
        id="card_1",
        category="geopolitics",
        headline="Key diplomatic agreement reached",
        summary="Two nations resolve border dispute peacefully.",
        why_it_matters="Reduces military tensions along eastern frontier.",
        canonical_url="https://example.com/news/1",
        source_name="Global Wire",
        source_domain="example.com"
    )
    briefing = NewsBriefing(
        briefing_id="b_1",
        domain="geopolitics",
        cards=[card]
    )

    temp_repo.cache_briefing(briefing, ttl_hours=1)
    retrieved = temp_repo.get_cached_briefing("geopolitics")
    assert retrieved is not None
    assert retrieved.is_cached is True
    assert len(retrieved.cards) == 1
    assert retrieved.cards[0].headline == "Key diplomatic agreement reached"
