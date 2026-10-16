"""Unit tests for MultiProviderLLMManager fallback chain and card visualizations."""

from datetime import datetime, timezone
import pytest
from app.services.llm import MultiProviderLLMManager, HeuristicAnalyzer, get_llm_manager
from app.schemas.article import NormalizedArticle, ExtractedPaper
from app.agents.cricket_agent import CricketDomainAgent
from app.agents.geopolitics_agent import GeopoliticsDomainAgent
from app.agents.ai_news_agent import AINewsDomainAgent


def test_heuristic_analyzer_structured_200_word_summary():
    """Verify deterministic 200-word structured summary generator."""
    analyzer = HeuristicAnalyzer()
    headline = "India win historic Test match by 295 runs in Perth"
    short_desc = "India registered an emphatic victory on day four with exceptional bowling from Jasprit Bumrah."
    content = "The visitors dominated all sessions, bowling Australia out for 238 in the second innings. Bumrah claimed eight wickets in the match."
    why_it_matters = "Massive boost for World Test Championship final qualification."

    summary = analyzer.build_structured_200_word_summary(
        headline=headline,
        short_desc=short_desc,
        content=content,
        domain="cricket",
        why_it_matters=why_it_matters,
        actors_or_subcat="Test Cricket"
    )

    words = summary.split()
    assert len(words) >= 60
    assert "India" in summary
    assert "World Test Championship" in summary
    assert len(summary.split("\n\n")) >= 2


def test_multi_provider_llm_manager_fallback_order():
    """Verify fallback chain returns heuristic when cloud APIs are unconfigured."""
    manager = MultiProviderLLMManager()
    pid, name, info = manager.get_preferred_engine_status()
    # In test environment with placeholder/empty keys, should resolve to heuristic or active local
    assert pid in ("groq", "gemini", "openai", "ollama", "heuristic")

    summary, provider = manager.generate_analytical_summary(
        headline="AI Model Released with Open Weights",
        short_desc="New open-weights model achieves 92% on reasoning benchmark.",
        content="Laboratory announced weights available under Apache 2.0 license.",
        domain="ai_news",
        why_it_matters="Enables local deployment on commodity hardware.",
        actors_or_subcat="Frontier Lab"
    )
    assert len(summary.split()) >= 40
    assert provider is not None


def test_all_domain_cards_have_table_data_and_charts():
    """Verify Cricket, Geopolitics, and AI cards have non-empty table_data and chart_metrics."""
    now = datetime.now(timezone.utc)

    # 1. Cricket Card
    cricket_art = NormalizedArticle(
        id="c1",
        title="India defeat Australia by 295 runs",
        canonical_url="https://cricinfo.com/1",
        source_name="ESPNcricinfo",
        source_domain="espncricinfo.com",
        published_at=now,
        category="cricket",
        short_description="Historic Test victory.",
        extracted_content_or_excerpt="Record victory in Perth.",
        content_fingerprint="c1_fp",
        importance_score=8.5
    )
    c_card = CricketDomainAgent().to_news_card(cricket_art)
    assert len(c_card.table_data) > 0
    assert len(c_card.chart_metrics) > 0
    assert "Historical Significance" in c_card.chart_metrics
    assert len(c_card.summary.split()) >= 30

    # 2. Geopolitics Card
    geo_art = NormalizedArticle(
        id="g1",
        title="India and France finalize defense strategic pact",
        canonical_url="https://thehindu.com/geo1",
        source_name="The Hindu",
        source_domain="thehindu.com",
        published_at=now,
        category="geopolitics",
        short_description="Strategic pact signed in New Delhi.",
        extracted_content_or_excerpt="Bilateral security pact between India and France.",
        content_fingerprint="g1_fp",
        importance_score=8.8
    )
    g_card = GeopoliticsDomainAgent().to_geopolitics_card(geo_art)
    assert len(g_card.table_data) > 0
    assert len(g_card.chart_metrics) > 0
    assert "Strategic Severity" in g_card.chart_metrics
    assert len(g_card.summary.split()) >= 30

    # 3. AI News Card (Research Paper)
    paper = ExtractedPaper(
        arxiv_id="2501.99999",
        title="Deep Reasoning Transformers",
        authors=["Author One"],
        published_date=now,
        abstract="Novel transformer architecture for multi-step reasoning.",
        primary_category="cs.AI",
        pdf_url="https://arxiv.org/pdf/2501.99999.pdf",
        abs_url="https://arxiv.org/abs/2501.99999"
    )
    ai_art = NormalizedArticle(
        id="a1",
        title="Deep Reasoning Transformers",
        canonical_url="https://arxiv.org/abs/2501.99999",
        source_name="arXiv",
        source_domain="arxiv.org",
        published_at=now,
        category="ai_news",
        short_description="Novel transformer architecture.",
        extracted_content_or_excerpt="Abstract on reasoning transformers.",
        content_fingerprint="a1_fp",
        importance_score=9.1,
        paper_data=paper
    )
    a_card = AINewsDomainAgent().to_ai_card(ai_art)
    assert len(a_card.table_data) > 0
    assert len(a_card.chart_metrics) > 0
    assert "Methodology Novelty" in a_card.chart_metrics
    assert len(a_card.summary.split()) >= 30
