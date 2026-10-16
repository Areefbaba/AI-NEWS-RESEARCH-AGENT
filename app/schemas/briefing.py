"""Briefing, card, and citation schemas for presentation and API responses."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CitationLink(BaseModel):
    """Clickable source citation link with verified provenance."""
    title: str
    url: str
    source_name: str
    published_date: Optional[str] = None


class NewsCard(BaseModel):
    """Standardized UI card presenting a qualified story."""
    id: str
    category: str                      # "cricket", "geopolitics", "ai_news"
    subcategory: Optional[str] = None  # e.g., "major_cricket", "test_cricket", "research_papers", etc.
    headline: str
    summary: str
    why_it_matters: str
    canonical_url: str
    source_name: str
    source_domain: str
    published_date: Optional[str] = None
    event_date: Optional[str] = None
    verification_status: str = "verified"  # "verified", "official_claim", "unconfirmed", "disputed"
    uncertainty_caveats: Optional[str] = None
    importance_score: float = 0.0
    ranking_rationale: Optional[str] = None
    supporting_citations: List[CitationLink] = Field(default_factory=list)

    # Geopolitics-specific structured fields
    what_happened: Optional[str] = None
    actors_involved: Optional[str] = None
    confirmed_vs_uncertain: Optional[str] = None
    india_implications: Optional[str] = None
    global_implications: Optional[str] = None

    # AI Research Paper specific structured fields
    paper_title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    research_problem: Optional[str] = None
    proposed_method: Optional[str] = None
    main_findings: Optional[str] = None
    limitations: Optional[str] = None
    practical_applications: Optional[str] = None
    engineer_takeaways: Optional[str] = None
    code_url: Optional[str] = None
    is_revision: bool = False

    # AI Model Launch specific structured fields
    model_name: Optional[str] = None
    developer: Optional[str] = None
    license_status: Optional[str] = None
    is_open_weights: Optional[bool] = None
    context_length: Optional[str] = None
    capabilities: Optional[str] = None

    # Cricket specific structured fields
    margin_or_score: Optional[str] = None
    historic_significance: Optional[str] = None
    is_confirmed_announcement: bool = True

    # Structured visualization data for tables and charts
    table_data: List[Dict[str, str]] = Field(default_factory=list)
    chart_metrics: Dict[str, float] = Field(default_factory=dict)


class NewsBriefing(BaseModel):
    """Complete synthesized news briefing payload."""
    briefing_id: str
    domain: str
    category_filter: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_cached: bool = False
    analysis_mode: str = "heuristic_fallback"  # "local_llm" or "heuristic_fallback"
    cards: List[NewsCard] = Field(default_factory=list)
    source_health_summary: Dict[str, str] = Field(default_factory=dict)
    total_sources_scanned: int = 0
    total_articles_evaluated: int = 0
    time_window_hours: int = 48
    notice_message: Optional[str] = None
