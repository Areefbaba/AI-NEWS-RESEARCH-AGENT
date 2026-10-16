"""Integration tests for LangGraph end-to-end workflow."""

import pytest
from app.graph.workflow import run_research_workflow
from app.schemas.briefing import NewsBriefing
from app.storage.database import Database
from app.storage.repository import ArticleRepository


def test_workflow_football_strictly_rejected():
    """Verify football section is rejected and returns error notice."""
    briefing = run_research_workflow(domain="football", bypass_cache=True)
    assert isinstance(briefing, NewsBriefing)
    assert len(briefing.cards) == 0
    assert "Football is strictly excluded" in (briefing.notice_message or "")


def test_workflow_unsupported_domain_rejected():
    briefing = run_research_workflow(domain="celebrity_gossip", bypass_cache=True)
    assert len(briefing.cards) == 0
    assert "Unsupported news domain" in (briefing.notice_message or "")


def test_workflow_cache_hit_behavior():
    # Pre-cache a briefing for cricket
    repo = ArticleRepository()
    mock_briefing = NewsBriefing(
        briefing_id="briefing_test_cache",
        domain="cricket",
        category_filter="test_cricket",
        cards=[]
    )
    repo.cache_briefing(mock_briefing, ttl_hours=2)

    # Calling with bypass_cache=False should hit cache
    res = run_research_workflow(
        domain="cricket",
        category_filter="test_cricket",
        bypass_cache=False
    )
    assert res.is_cached is True
    assert res.briefing_id == "briefing_test_cache"


def test_individual_graph_nodes():
    from app.graph.nodes import (
        validate_request_node,
        normalize_articles_node,
        deduplicate_cluster_node,
        rank_and_filter_node,
        generate_briefing_node,
        output_guardrails_node
    )
    from app.schemas.article import RawArticle

    # 1. validate_request_node
    val_res = validate_request_node({"domain": "cricket", "time_window_hours": 48})
    assert val_res["is_valid_request"] is True

    # 2. normalize_articles_node
    raw = RawArticle(
        source_id="test_src",
        source_name="Test Source",
        source_domain="test.com",
        url="https://test.com/story1",
        title="India win historic Test match by 250 runs",
        summary_raw="Decisive match summary.",
        content_raw="Full body of test win."
    )
    state = {
        "domain": "cricket",
        "time_window_hours": 48,
        "raw_articles": [raw.model_dump()],
        "briefing": None
    }
    norm_res = normalize_articles_node(state)
    assert len(norm_res["normalized_articles"]) == 1

    # 3. deduplicate_cluster_node
    state["normalized_articles"] = norm_res["normalized_articles"]
    dedup_res = deduplicate_cluster_node(state)
    assert len(dedup_res["clustered_stories"]) == 1

    # 4. rank_and_filter_node
    state["clustered_stories"] = dedup_res["clustered_stories"]
    rank_res = rank_and_filter_node(state)
    assert len(rank_res["ranked_articles"]) == 1

    # 5. generate_briefing_node
    state["ranked_articles"] = rank_res["ranked_articles"]
    state["category_filter"] = "test_cricket"
    gen_res = generate_briefing_node(state)
    assert gen_res["briefing"] is not None

    # 6. output_guardrails_node
    state["briefing"] = gen_res["briefing"]
    guard_res = output_guardrails_node(state)
    assert guard_res["execution_metadata"]["cards_count"] >= 1
