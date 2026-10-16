"""LangGraph State definition for the intelligence research workflow."""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Immutable state dictionary flowing through the LangGraph workflow."""

    # Input parameters
    domain: str                         # "cricket", "geopolitics", "ai_news"
    category_filter: Optional[str]      # e.g., "test_cricket", "research_papers", etc.
    time_window_hours: int              # default 48
    query: Optional[str]                # optional filter query
    bypass_cache: bool                  # force fresh fetch if True

    # Validation & Routing
    is_valid_request: bool
    error_message: Optional[str]

    # Ingestion & pipeline state
    source_configs: List[Dict[str, Any]]
    raw_articles: List[Dict[str, Any]]
    normalized_articles: List[Dict[str, Any]]
    clustered_stories: List[Dict[str, Any]]
    ranked_articles: List[Dict[str, Any]]

    # Output briefing
    briefing: Optional[Dict[str, Any]]
    source_health_summary: Dict[str, str]
    execution_metadata: Dict[str, Any]
