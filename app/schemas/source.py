"""Source configuration and health tracking schemas."""

from enum import Enum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class TrustLevel(str, Enum):
    """Source trust classification."""
    OFFICIAL = "official"     # e.g., ICC, BCCI, UN, White House, MEA, arXiv
    HIGH = "high"             # e.g., Reuters, BBC, ESPNcricinfo, The Hindu, Nature
    MEDIUM = "medium"         # e.g., established tech blogs, syndicated wire news


class SourceType(str, Enum):
    """Type of source retrieval adapter."""
    RSS = "rss"
    API = "api"
    SEARCH = "search"


class NewsDomain(str, Enum):
    """Exact news domains supported by the application."""
    CRICKET = "cricket"
    GEOPOLITICS = "geopolitics"
    AI_NEWS = "ai_news"


class SourceConfig(BaseModel):
    """Configuration for an individual trusted feed or endpoint."""
    source_id: str
    name: str
    url: str
    domain: str
    trust_level: TrustLevel = TrustLevel.HIGH
    source_type: SourceType = SourceType.RSS
    news_domains: List[NewsDomain]
    subcategories: List[str] = Field(default_factory=list)
    is_active: bool = True
    priority: int = 1
    timeout_seconds: float = 12.0
    trust_rationale: Optional[str] = None


class SourceHealth(BaseModel):
    """Telemetry and health status for an external source."""
    source_id: str
    name: str
    status: str = "healthy"  # "healthy", "degraded", "failing"
    last_attempt: Optional[datetime] = None
    last_success: Optional[datetime] = None
    error_message: Optional[str] = None
    latency_ms: Optional[float] = None
    items_fetched: int = 0
