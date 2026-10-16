"""Data models for raw, normalized, and research articles."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RawArticle(BaseModel):
    """Raw ingestion payload directly from an RSS entry, API item, or search hit."""
    source_id: str
    source_name: str
    source_domain: str
    url: str
    title: str
    summary_raw: Optional[str] = None
    content_raw: Optional[str] = None
    author: Optional[str] = None
    published_raw: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extra_metadata: Dict[str, str] = Field(default_factory=dict)


class ExtractedPaper(BaseModel):
    """Specialized metadata for arXiv and academic research papers."""
    arxiv_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    published_date: datetime
    updated_date: Optional[datetime] = None
    is_revision: bool = False
    abstract: str
    primary_category: str
    categories: List[str] = Field(default_factory=list)
    pdf_url: str
    abs_url: str
    doi: Optional[str] = None
    journal_ref: Optional[str] = None
    research_problem: Optional[str] = None
    proposed_method: Optional[str] = None
    main_findings: Optional[str] = None
    limitations: Optional[str] = None
    practical_applications: Optional[str] = None
    engineer_takeaways: Optional[str] = None
    code_url: Optional[str] = None


class NormalizedArticle(BaseModel):
    """Cleaned, validated, and normalized article data structure."""
    id: str
    title: str
    canonical_url: str
    source_name: str
    source_domain: str
    published_at: Optional[datetime] = None
    event_date: Optional[datetime] = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    category: str
    subcategory: Optional[str] = None
    region: Optional[str] = None
    short_description: str
    extracted_content_or_excerpt: str
    key_claims: List[str] = Field(default_factory=list)
    supporting_sources: List[Dict[str, str]] = Field(default_factory=list)
    related_story_ids: List[str] = Field(default_factory=list)
    importance_score: float = 0.0
    recency_score: float = 0.0
    source_quality_score: float = 0.0
    verification_status: str = "unconfirmed"  # verified, unconfirmed, official_claim, disputed
    uncertainty_notes: Optional[str] = None
    ai_analysis: Optional[str] = None
    content_fingerprint: str
    ranking_explanation: Optional[str] = None

    # AI research extensions (if applicable)
    paper_data: Optional[ExtractedPaper] = None

    # Model release extensions (if applicable)
    developer: Optional[str] = None
    license_status: Optional[str] = None
    is_open_weights: Optional[bool] = None
    context_length: Optional[str] = None
    hardware_or_serving_requirements: Optional[str] = None
