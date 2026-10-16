"""Unit tests for domain policies: Cricket, Geopolitics, and AI News."""

from datetime import datetime, timezone
import pytest
from app.agents.cricket_agent import CricketDomainAgent
from app.agents.geopolitics_agent import GeopoliticsDomainAgent
from app.agents.ai_news_agent import AINewsDomainAgent
from app.schemas.article import NormalizedArticle, ExtractedPaper


def make_article(title, desc, domain, source="Reuters", is_paper=False):
    paper = None
    if is_paper:
        paper = ExtractedPaper(
            arxiv_id="2610.12345v1",
            title=title,
            authors=["Alice", "Bob"],
            published_date=datetime.now(timezone.utc),
            abstract=desc,
            primary_category="cs.AI",
            pdf_url="https://arxiv.org/pdf/2610.12345v1.pdf",
            abs_url="https://arxiv.org/abs/2610.12345v1"
        )
    return NormalizedArticle(
        id="art_test",
        title=title,
        canonical_url="https://example.com/test",
        source_name=source,
        source_domain="example.com",
        published_at=datetime.now(timezone.utc),
        category=domain,
        short_description=desc,
        extracted_content_or_excerpt=desc,
        content_fingerprint="fp_123",
        paper_data=paper
    )


# --- CRICKET DOMAIN TESTS ---

def test_cricket_routine_scorecard_filtering():
    agent = CricketDomainAgent()
    routine = make_article("Ranji Trophy Day 3: Delhi 180/6 vs Mumbai, ball by ball commentary", "Routine match summary", "cricket")
    assert agent.is_routine_scorecard(routine) is True

    historic = make_article("India win historic Test match against Australia by 295 runs", "Historic victory", "cricket")
    assert agent.is_routine_scorecard(historic) is False


def test_cricket_retirement_rumor_vs_confirmed():
    agent = CricketDomainAgent()
    rumor = make_article("Rumours swirl that veteran batter may retire after England series", "Speculation mounts", "cricket")
    assert agent.is_confirmed_player_announcement(rumor) is False

    confirmed = make_article("Legendary all-rounder officially announces retirement from international cricket", "ICC confirms retirement", "cricket", "ICC")
    assert agent.is_confirmed_player_announcement(confirmed) is True


def test_cricket_subcategory_classification():
    agent = CricketDomainAgent()
    test_art = make_article("World Test Championship final: Decisive bowling spell secures trophy", "Red-ball cricket", "cricket")
    assert agent.classify_subcategory(test_art) == "test_cricket"

    player_art = make_article("Star fast bowler appointed captain for upcoming season", "Captaincy announcement", "cricket")
    assert agent.classify_subcategory(player_art) == "player_updates"


# --- GEOPOLITICS DOMAIN TESTS ---

def test_geopolitics_actors_and_allegations():
    agent = GeopoliticsDomainAgent()
    allegation_art = make_article(
        "US and European Union announce new sanctions as State Department alleges treaty violations",
        "Officials claim breaches occurred near border.",
        "geopolitics"
    )
    actors = agent.detect_actors(f"{allegation_art.title}. {allegation_art.short_description}")
    assert "United States" in actors or "US" in actors
    assert "European Union" in actors

    status, caveat = agent.detect_uncertainty_and_allegations(f"{allegation_art.title}. {allegation_art.short_description}")
    assert status == "official_claim"
    assert "allegations" in caveat.lower()


def test_geopolitics_india_implications():
    agent = GeopoliticsDomainAgent()
    india_defense = make_article(
        "India and France finalize defense partnership on advanced jet engines",
        "New Delhi expands strategic defense agreements.",
        "geopolitics"
    )
    card = agent.to_geopolitics_card(india_defense)
    assert card.india_implications is not None
    assert "defense" in card.india_implications.lower()

    unrelated = make_article(
        "Chile and Argentina resolve localized water rights agreement",
        "Regional pact finalized.",
        "geopolitics"
    )
    card_unrelated = agent.to_geopolitics_card(unrelated)
    assert card_unrelated.india_implications is None, "Should not fabricate India implications where none exist"


# --- AI NEWS & RESEARCH DOMAIN TESTS ---

def test_ai_paper_card_generation():
    agent = AINewsDomainAgent()
    paper_art = make_article(
        "Self-Correction in LLMs via Dynamic Search",
        "We introduce an adaptive beam search algorithm improving reasoning accuracy.",
        "ai_news",
        source="arXiv",
        is_paper=True
    )
    card = agent.to_ai_card(paper_art)
    assert card.subcategory == "research_papers"
    assert "Alice" in card.authors
    assert card.code_url is not None
    assert "arXiv" in card.why_it_matters


def test_ai_model_launch_detection():
    agent = AINewsDomainAgent()
    launch_art = make_article(
        "Meta AI releases Llama 3.3 weights with permissive license",
        "The open-weight model weights are now available on Hugging Face.",
        "ai_news"
    )
    card = agent.to_ai_card(launch_art)
    assert card.subcategory == "model_launches"
    assert card.developer == "Meta AI"
    assert card.is_open_weights is True
