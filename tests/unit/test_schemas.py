"""Unit tests for Pydantic schemas."""

from datetime import datetime, timezone
import pytest
from app.schemas.source import TrustLevel, SourceType, NewsDomain, SourceConfig, SourceHealth
from app.schemas.article import NormalizedArticle, RawArticle, ExtractedPaper
from app.schemas.briefing import NewsCard, NewsBriefing, CitationLink


def test_source_config_validation():
    config = SourceConfig(
        source_id="test_reuters",
        name="Reuters World News",
        url="https://feeds.reuters.com/reuters/worldNews",
        domain="reuters.com",
        trust_level=TrustLevel.HIGH,
        source_type=SourceType.RSS,
        news_domains=[NewsDomain.GEOPOLITICS]
    )
    assert config.source_id == "test_reuters"
    assert config.trust_level == TrustLevel.HIGH
    assert config.is_active is True
    assert NewsDomain.GEOPOLITICS in config.news_domains


def test_normalized_article_serialization():
    now = datetime.now(timezone.utc)
    article = NormalizedArticle(
        id="art_123",
        title="Major Breakthrough in Long Context LLM Reasoning",
        canonical_url="https://example.com/ai-paper-123",
        source_name="AI Research Daily",
        source_domain="example.com",
        published_at=now,
        retrieved_at=now,
        category="ai_news",
        subcategory="research_papers",
        short_description="Researchers demonstrate a novel architectural optimization for 1M context.",
        extracted_content_or_excerpt="Full excerpt content here.",
        content_fingerprint="abc123fingerprint",
        importance_score=0.88,
        verification_status="verified"
    )
    data_json = article.model_dump_json()
    assert "Major Breakthrough" in data_json
    reloaded = NormalizedArticle.model_validate_json(data_json)
    assert reloaded.title == article.title
    assert reloaded.importance_score == 0.88


def test_news_card_and_briefing():
    citation = CitationLink(
        title="Original Source",
        url="https://example.com/source",
        source_name="Example News"
    )
    card = NewsCard(
        id="card_1",
        category="cricket",
        subcategory="major_cricket",
        headline="Historic Win by 200 Runs",
        summary="A decisive outcome in tournament final.",
        why_it_matters="Marks the largest margin in history.",
        canonical_url="https://example.com/cricket-win",
        source_name="Cricinfo",
        source_domain="espncricinfo.com",
        supporting_citations=[citation]
    )
    briefing = NewsBriefing(
        briefing_id="briefing_999",
        domain="cricket",
        cards=[card],
        total_sources_scanned=5,
        total_articles_evaluated=12
    )
    assert len(briefing.cards) == 1
    assert briefing.cards[0].headline == "Historic Win by 200 Runs"
    assert len(briefing.cards[0].supporting_citations) == 1
