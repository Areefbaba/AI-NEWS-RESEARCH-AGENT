"""Unit tests for ReportGenerator and full card formatting."""

from datetime import datetime, timezone
import pytest
from app.services.report_generator import ReportGenerator
from app.schemas.article import NormalizedArticle, ExtractedPaper
from app.agents.cricket_agent import CricketDomainAgent


def test_cricket_card_conversion_and_briefing():
    art = NormalizedArticle(
        id="art_c1",
        title="India win historic Test match by 200 runs",
        canonical_url="https://cricinfo.com/match-1",
        source_name="ESPNcricinfo",
        source_domain="espncricinfo.com",
        published_at=datetime.now(timezone.utc),
        category="cricket",
        subcategory="test_cricket",
        short_description="Decisive series sweep completed.",
        extracted_content_or_excerpt="Full excerpt of historic Test match.",
        content_fingerprint="fp_c1",
        importance_score=0.88,
        verification_status="verified",
        ranking_explanation="Historic margin record."
    )

    agent = CricketDomainAgent()
    card = agent.to_news_card(art)
    assert card.subcategory == "test_cricket"
    assert card.is_confirmed_announcement is True
    assert len(card.supporting_citations) >= 1

    generator = ReportGenerator()
    briefing = generator.generate_briefing(
        domain="cricket",
        articles=[art],
        category_filter="test_cricket",
        total_sources=3,
        total_evaluated=5
    )
    assert briefing.domain == "cricket"
    assert len(briefing.cards) == 1
    assert briefing.cards[0].headline == art.title


def test_geopolitics_and_ai_briefing_generation():
    geo_art = NormalizedArticle(
        id="art_g1",
        title="India and France finalize defense strategic pact",
        canonical_url="https://thehindu.com/defense",
        source_name="The Hindu",
        source_domain="thehindu.com",
        published_at=datetime.now(timezone.utc),
        category="geopolitics",
        short_description="Landmark security agreement.",
        extracted_content_or_excerpt="Full text of defense pact with India.",
        content_fingerprint="fp_g1",
        importance_score=0.85
    )

    paper = ExtractedPaper(
        arxiv_id="2610.88888v1",
        title="Reasoning Scaling in Frontier Models",
        authors=["Alice Researcher"],
        published_date=datetime.now(timezone.utc),
        abstract="We demonstrate scaling laws for test-time compute.",
        primary_category="cs.AI",
        pdf_url="https://arxiv.org/pdf/2610.88888v1.pdf",
        abs_url="https://arxiv.org/abs/2610.88888v1"
    )
    ai_art = NormalizedArticle(
        id="art_a1",
        title="Reasoning Scaling in Frontier Models",
        canonical_url="https://arxiv.org/abs/2610.88888v1",
        source_name="arXiv",
        source_domain="arxiv.org",
        published_at=datetime.now(timezone.utc),
        category="ai_news",
        short_description="Scaling laws for test-time compute.",
        extracted_content_or_excerpt="Paper abstract.",
        content_fingerprint="fp_a1",
        importance_score=0.91,
        paper_data=paper
    )

    generator = ReportGenerator()

    geo_briefing = generator.generate_briefing(
        domain="geopolitics",
        articles=[geo_art],
        total_sources=2,
        total_evaluated=2
    )
    assert len(geo_briefing.cards) == 1
    assert geo_briefing.cards[0].india_implications is not None

    ai_briefing = generator.generate_briefing(
        domain="ai_news",
        articles=[ai_art],
        total_sources=2,
        total_evaluated=2
    )
    assert len(ai_briefing.cards) == 1
    assert ai_briefing.cards[0].subcategory == "research_papers"
    assert "Alice Researcher" in ai_briefing.cards[0].authors
