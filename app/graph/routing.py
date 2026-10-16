"""Conditional routing edges for LangGraph workflow."""

from app.graph.state import AgentState


def check_request_validity(state: AgentState) -> str:
    """Route to cache check if valid, or terminate if invalid."""
    if not state.get("is_valid_request", False):
        return "invalid"
    return "valid"


def check_cache_hit(state: AgentState) -> str:
    """If briefing is already present in cache, bypass collection and jump to guardrails."""
    if state.get("briefing") is not None:
        return "cache_hit"
    return "cache_miss"
