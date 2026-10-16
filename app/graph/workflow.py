"""LangGraph StateGraph construction and execution."""

import logging
from typing import Optional
from langgraph.graph import StateGraph, START, END

from app.graph.state import AgentState
from app.graph.nodes import (
    validate_request_node,
    check_cache_node,
    collect_sources_node,
    normalize_articles_node,
    deduplicate_cluster_node,
    rank_and_filter_node,
    generate_briefing_node,
    output_guardrails_node,
)
from app.graph.routing import check_request_validity, check_cache_hit
from app.schemas.briefing import NewsBriefing

logger = logging.getLogger(__name__)


def create_news_graph():
    """Build and compile the LangGraph news intelligence workflow."""
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("validate_request", validate_request_node)
    workflow.add_node("check_cache", check_cache_node)
    workflow.add_node("collect_sources", collect_sources_node)
    workflow.add_node("normalize_articles", normalize_articles_node)
    workflow.add_node("deduplicate_cluster", deduplicate_cluster_node)
    workflow.add_node("rank_and_filter", rank_and_filter_node)
    workflow.add_node("generate_briefing", generate_briefing_node)
    workflow.add_node("output_guardrails", output_guardrails_node)

    # Edge: Start -> validate_request
    workflow.add_edge(START, "validate_request")

    # Conditional Edge: validate_request -> check_cache OR END
    workflow.add_conditional_edges(
        "validate_request",
        check_request_validity,
        {
            "valid": "check_cache",
            "invalid": END,
        }
    )

    # Conditional Edge: check_cache -> output_guardrails (hit) OR collect_sources (miss)
    workflow.add_conditional_edges(
        "check_cache",
        check_cache_hit,
        {
            "cache_hit": "output_guardrails",
            "cache_miss": "collect_sources",
        }
    )

    # Pipeline linear sequence
    workflow.add_edge("collect_sources", "normalize_articles")
    workflow.add_edge("normalize_articles", "deduplicate_cluster")
    workflow.add_edge("deduplicate_cluster", "rank_and_filter")
    workflow.add_edge("rank_and_filter", "generate_briefing")
    workflow.add_edge("generate_briefing", "output_guardrails")
    workflow.add_edge("output_guardrails", END)

    return workflow.compile()


_cached_compiled_graph = None


def get_compiled_graph():
    """Singleton getter for compiled LangGraph."""
    global _cached_compiled_graph
    if _cached_compiled_graph is None:
        _cached_compiled_graph = create_news_graph()
    return _cached_compiled_graph


def run_research_workflow(
    domain: str,
    category_filter: Optional[str] = None,
    time_window_hours: int = 48,
    bypass_cache: bool = False,
    query: Optional[str] = None
) -> NewsBriefing:
    """Execute end-to-end research workflow and return structured NewsBriefing."""
    graph = get_compiled_graph()

    initial_state: AgentState = {
        "domain": domain,
        "category_filter": category_filter,
        "time_window_hours": time_window_hours,
        "query": query,
        "bypass_cache": bypass_cache,
        "is_valid_request": False,
        "error_message": None,
        "source_configs": [],
        "raw_articles": [],
        "normalized_articles": [],
        "clustered_stories": [],
        "ranked_articles": [],
        "briefing": None,
        "source_health_summary": {},
        "execution_metadata": {}
    }

    result = graph.invoke(initial_state)

    if not result.get("is_valid_request", False):
        err = result.get("error_message") or "Request validation failed."
        return NewsBriefing(
            briefing_id="err_briefing",
            domain=domain,
            cards=[],
            notice_message=err
        )

    briefing_dict = result.get("briefing")
    if briefing_dict:
        return NewsBriefing.model_validate(briefing_dict)

    return NewsBriefing(
        briefing_id="empty_briefing",
        domain=domain,
        cards=[],
        notice_message="No qualifying news found for this criteria."
    )
