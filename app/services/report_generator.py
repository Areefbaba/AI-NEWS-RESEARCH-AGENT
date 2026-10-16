"""Report and briefing synthesis service combining domain agents and intelligence engine."""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.article import NormalizedArticle
from app.schemas.briefing import NewsBriefing, NewsCard
from app.agents.cricket_agent import CricketDomainAgent
from app.agents.geopolitics_agent import GeopoliticsDomainAgent
from app.agents.ai_news_agent import AINewsDomainAgent
from app.services.llm import get_analysis_mode, HeuristicAnalyzer

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Transforms qualified domain articles into a synthesized, verifiable NewsBriefing."""

    def __init__(self):
        self.cricket_agent = CricketDomainAgent()
        self.geopolitics_agent = GeopoliticsDomainAgent()
        self.ai_agent = AINewsDomainAgent()

    def generate_briefing(
        self,
        domain: str,
        articles: List[NormalizedArticle],
        category_filter: Optional[str] = None,
        source_health_summary: Optional[Dict[str, str]] = None,
        total_sources: int = 0,
        total_evaluated: int = 0,
        time_window_hours: int = 48
    ) -> NewsBriefing:
        """Construct full news briefing using appropriate domain policy."""
        mode, ollama_client = get_analysis_mode()
        cards: List[NewsCard] = []

        domain_lower = domain.lower()

        if domain_lower == "cricket":
            # Apply cricket filters and classification
            qualified = self.cricket_agent.filter_and_process(articles, subcategory_filter=category_filter)
            for art in qualified:
                cards.append(self.cricket_agent.to_news_card(art))

        elif domain_lower == "geopolitics":
            # Filter up to 5 top stories maximum
            for art in articles[:5]:
                cards.append(self.geopolitics_agent.to_geopolitics_card(art))

        elif domain_lower == "ai_news":
            # Filter up to 5 top stories maximum per category or overall
            for art in articles[:5]:
                cards.append(self.ai_agent.to_ai_card(art))

        # Check if fewer than 5 qualified stories
        notice = None
        if len(cards) < 5 and domain_lower in ("geopolitics", "ai_news"):
            notice = f"Only {len(cards)} stories met the strict evidence and quality thresholds. Showing verified stories without padding."

        briefing_id = f"briefing_{uuid.uuid4().hex[:10]}"

        return NewsBriefing(
            briefing_id=briefing_id,
            domain=domain_lower,
            category_filter=category_filter,
            generated_at=datetime.now(timezone.utc),
            is_cached=False,
            analysis_mode=mode,
            cards=cards,
            source_health_summary=source_health_summary or {},
            total_sources_scanned=total_sources,
            total_articles_evaluated=total_evaluated,
            time_window_hours=time_window_hours,
            notice_message=notice
        )
