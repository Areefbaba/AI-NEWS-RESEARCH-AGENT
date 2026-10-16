"""Unit tests for sources, adapters, and source registry."""

import pytest
from app.schemas.source import NewsDomain, SourceConfig, TrustLevel, SourceType
from app.sources.source_registry import SourceRegistry, get_default_source_registry
from app.sources.rss_reader import RSSReaderAdapter
from app.sources.ai_research_sources import ArxivSourceAdapter
from app.sources.article_extractor import clean_html_text
from app.sources.web_search import get_search_provider, NoOpSearchProvider
from app.storage.database import Database
from app.storage.repository import ArticleRepository


SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Cricket Test Feed</title>
    <link>https://example.com/cricket</link>
    <item>
      <title>India win historic Test match by 317 runs</title>
      <link>https://example.com/cricket/test-win-317</link>
      <description>India produced a dominant performance to claim victory.</description>
      <pubDate>Mon, 12 Oct 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

SAMPLE_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>arXiv Search</title>
  <entry>
    <id>http://arxiv.org/abs/2610.99999v1</id>
    <title>Scalable Agentic Tool Use with Efficient Reasoning</title>
    <summary>We introduce a novel reasoning architecture that reduces tool latency.</summary>
    <published>2026-10-10T12:00:00Z</published>
    <updated>2026-10-10T12:00:00Z</updated>
    <author><name>Jane Doe</name></author>
    <author><name>John Smith</name></author>
    <arxiv:primary_category term="cs.AI"/>
    <link href="http://arxiv.org/abs/2610.99999v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2610.99999v1" rel="related" type="application/pdf"/>
  </entry>
</feed>
"""


def test_source_registry_domains():
    registry = get_default_source_registry()

    # Cricket sources exist
    cricket_sources = registry.get_sources_for_domain("cricket")
    assert len(cricket_sources) >= 3

    # Geopolitics sources exist
    geo_sources = registry.get_sources_for_domain("geopolitics")
    assert len(geo_sources) >= 3

    # AI sources exist
    ai_sources = registry.get_sources_for_domain("ai_news")
    assert len(ai_sources) >= 3

    # NO football sources anywhere
    all_sources = registry.get_all_sources()
    for s in all_sources:
        for domain in s.news_domains:
            assert domain.value != "football", "Football must not exist in registered domains"
            assert "football" not in s.name.lower()


def test_html_cleaning():
    dirty_html = """
    <div>
        <script>alert('malicious')</script>
        <p>This is a <b>critical</b> news statement.</p>
        <style>.hide { display: none; }</style>
    </div>
    """
    clean = clean_html_text(dirty_html)
    assert "alert" not in clean
    assert "critical news statement." in clean


def test_rss_reader_with_cached_content(monkeypatch):
    db = Database(db_path=":memory:")
    repo = ArticleRepository(db=db)

    config = SourceConfig(
        source_id="mock_cricket",
        name="Mock Cricket Feed",
        url="https://example.com/rss",
        domain="example.com",
        news_domains=[NewsDomain.CRICKET]
    )

    # Pre-populate cache
    repo.set_feed_cache(config.url, SAMPLE_RSS_XML, ttl_hours=2)

    reader = RSSReaderAdapter(repo=repo)
    articles = reader.fetch(config)

    assert len(articles) == 1
    assert articles[0].title == "India win historic Test match by 317 runs"
    assert articles[0].url == "https://example.com/cricket/test-win-317"


def test_arxiv_adapter_with_cached_content():
    db = Database(db_path=":memory:")
    repo = ArticleRepository(db=db)

    config = SourceConfig(
        source_id="mock_arxiv",
        name="Mock arXiv",
        url="http://export.arxiv.org/api/query?mock=true",
        domain="arxiv.org",
        news_domains=[NewsDomain.AI_NEWS]
    )

    repo.set_feed_cache(config.url, SAMPLE_ARXIV_XML, ttl_hours=2)

    adapter = ArxivSourceAdapter(repo=repo)
    articles = adapter.fetch(config)

    assert len(articles) == 1
    art = articles[0]
    assert art.title == "Scalable Agentic Tool Use with Efficient Reasoning"
    assert "Jane Doe" in art.author
    assert art.extra_metadata.get("arxiv_id") == "2610.99999v1"
    assert art.extra_metadata.get("is_paper") == "true"


def test_noop_search_provider():
    provider = get_search_provider()
    assert isinstance(provider, NoOpSearchProvider)
    results = provider.search("test query")
    assert results == []
