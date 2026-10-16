"""Cricket Domain Agent: Enforces policies for Major, Test, International Matches, and Player Updates."""

import re
import logging
from typing import Dict, List, Optional
from app.schemas.article import NormalizedArticle
from app.schemas.briefing import NewsCard, CitationLink

logger = logging.getLogger(__name__)

ROUTINE_SCORECARD_PATTERNS = [
    r"live score", r"ball-by-ball", r"ball by ball", r"scorecard", r"playing xi",
    r"toss update", r"innings break", r"lunch update", r"tea update", r"stumps day \d",
    r"day \d: \w+ \d+/\d+", r"ranji trophy day", r"overs: \d+", r"fantasy cricket tips"
]

RUMOR_PATTERNS = [
    r"\brumou?rs?\b", r"\bspeculat(ion|ed|ing)\b", r"\bmay retire\b",
    r"\blikely to step down\b", r"\bcloud over future\b", r"\bunconfirmed\b"
]

TEST_CRICKET_KEYWORDS = [
    "test match", "test series", "ashes", "border-gavaskar", "world test championship",
    "wtc", "red-ball", "5-day match", "follow-on", "clean sweep in test"
]

PLAYER_UPDATE_KEYWORDS = [
    "retires", "retirement", "steps down", "quits", "comeback", "ruled out",
    "appointed captain", "bcci contract", "central contract", "career", "surgery"
]

INTERNATIONAL_MATCH_KEYWORDS = [
    "world cup", "champions trophy", "t20i", "odi", "series victory", "upset",
    "qualification", "eliminated", "super eight", "semi-final", "final", "hat-trick"
]


class CricketDomainAgent:
    """Applies strict editorial inclusion/exclusion policies for Cricket News."""

    def is_routine_scorecard(self, article: NormalizedArticle) -> bool:
        """Detect whether article is a routine scorecard or ball-by-ball commentary."""
        text = f"{article.title} {article.short_description}".lower()
        for pat in ROUTINE_SCORECARD_PATTERNS:
            if re.search(pat, text):
                return True
        return False

    def is_confirmed_player_announcement(self, article: NormalizedArticle) -> bool:
        """Check whether retirement or player update is confirmed vs speculative rumor."""
        text = f"{article.title} {article.short_description}".lower()
        for pat in RUMOR_PATTERNS:
            if re.search(pat, text):
                return False
        return True

    def classify_subcategory(self, article: NormalizedArticle) -> str:
        """Classify a cricket story into one of the 4 designated subcategories."""
        text = f"{article.title} {article.short_description}".lower()

        # 1. Player updates check
        if any(kw in text for kw in PLAYER_UPDATE_KEYWORDS):
            return "player_updates"

        # 2. Test cricket check
        if any(kw in text for kw in TEST_CRICKET_KEYWORDS):
            return "test_cricket"

        # 3. International match check
        if any(kw in text for kw in INTERNATIONAL_MATCH_KEYWORDS):
            return "international_matches"

        # 4. Default to major cricket news
        return "major_cricket"

    def filter_and_process(
        self,
        articles: List[NormalizedArticle],
        subcategory_filter: Optional[str] = None
    ) -> List[NormalizedArticle]:
        """Filter out routine scorecards and unconfirmed rumors, classifying eligible stories."""
        qualified: List[NormalizedArticle] = []

        for article in articles:
            # Policy 1: Exclude routine scorecards
            if self.is_routine_scorecard(article):
                logger.debug("Rejected routine scorecard: %s", article.title)
                continue

            subcat = self.classify_subcategory(article)
            article.subcategory = subcat

            # Policy 2: Check rumor status for player updates
            if subcat == "player_updates":
                confirmed = self.is_confirmed_player_announcement(article)
                if not confirmed:
                    # Rumors must not be presented as confirmed news
                    article.verification_status = "unconfirmed"
                    article.uncertainty_notes = "Speculative reporting / unconfirmed rumor"

            # Apply subcategory filter if specified
            if subcategory_filter and subcategory_filter != "all":
                if subcat != subcategory_filter:
                    continue

            qualified.append(article)

        return qualified

    def to_news_card(self, article: NormalizedArticle) -> NewsCard:
        """Transform a qualified cricket article into a presentation-ready NewsCard with 200-word summary, table, and charts."""
        from app.services.llm import get_llm_manager

        subcat = article.subcategory or "major_cricket"
        subcat_labels = {
            "major_cricket": "Major Cricket Milestone",
            "test_cricket": "Decisive Test Cricket Development",
            "international_matches": "Key International Match Outcome",
            "player_updates": "Official Player Announcement"
        }

        why_it_matters = article.ranking_explanation or "Significant development impacting world and Indian cricket."
        if subcat == "player_updates" and article.verification_status == "unconfirmed":
            why_it_matters = "Unconfirmed speculation; official board or player statement pending."

        # Generate ~200-word structured analytical summary
        llm_mgr = get_llm_manager()
        summary_text, _ = llm_mgr.generate_analytical_summary(
            headline=article.title,
            short_desc=article.short_description,
            content=article.extracted_content_or_excerpt,
            domain="cricket",
            why_it_matters=why_it_matters,
            actors_or_subcat=subcat_labels.get(subcat, "Cricket")
        )

        citations = [
            CitationLink(
                title=s.get("title", article.title),
                url=s.get("url", article.canonical_url),
                source_name=s.get("source_name", article.source_name),
                published_date=s.get("published_date")
            )
            for s in article.supporting_sources
        ]
        if not citations:
            citations = [
                CitationLink(
                    title=article.title,
                    url=article.canonical_url,
                    source_name=article.source_name,
                    published_date=article.published_at.isoformat() if article.published_at else None
                )
            ]

        # Structured Table Data
        status_label = "Confirmed Official" if article.verification_status != "unconfirmed" else "Unverified Report"
        table_data = [
            {"Dimension": "Category / Format", "Details": subcat_labels.get(subcat, "Cricket News")},
            {"Dimension": "Event Significance", "Details": "Decisive Historical Milestone" if article.importance_score > 6.0 else "Major Tournament Development"},
            {"Dimension": "Primary Source", "Details": f"{article.source_name} ({article.source_domain})"},
            {"Dimension": "Verification Status", "Details": status_label},
            {"Dimension": "Chronology", "Details": article.published_at.strftime("%Y-%m-%d %H:%M UTC") if article.published_at else "Current Window"}
        ]

        # Normalized Chart Metrics (Scale 1.0 - 10.0)
        base_score = max(5.0, min(9.5, article.importance_score if article.importance_score > 0 else 7.5))
        chart_metrics = {
            "Historical Significance": round(min(9.8, base_score + 0.6), 1),
            "Decisive Margin / Record": round(min(9.5, base_score + 0.2), 1),
            "Tournament / WTC Impact": round(min(9.6, base_score + 0.4), 1),
            "Source Corroboration": round(min(9.9, base_score + 0.8), 1)
        }

        return NewsCard(
            id=article.id,
            category="cricket",
            subcategory=subcat,
            headline=article.title,
            summary=summary_text,
            why_it_matters=why_it_matters,
            canonical_url=article.canonical_url,
            source_name=article.source_name,
            source_domain=article.source_domain,
            published_date=article.published_at.strftime("%Y-%m-%d %H:%M UTC") if article.published_at else "Recent",
            event_date=article.event_date.strftime("%Y-%m-%d") if article.event_date else None,
            verification_status=article.verification_status,
            uncertainty_caveats=article.uncertainty_notes,
            importance_score=article.importance_score,
            ranking_rationale=article.ranking_explanation,
            supporting_citations=citations,
            is_confirmed_announcement=(article.verification_status != "unconfirmed"),
            table_data=table_data,
            chart_metrics=chart_metrics
        )
