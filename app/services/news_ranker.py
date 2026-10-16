"""Explainable multi-factor importance ranking engine."""

import re
import math
import logging
from datetime import datetime, timezone
from typing import List, Tuple
from app.config import get_settings
from app.schemas.article import NormalizedArticle
from app.services.deduplication import StoryCluster

logger = logging.getLogger(__name__)

# Keywords signaling high impact
CRICKET_HIGH_IMPACT = {
    "historic", "world cup", "record", "clean sweep", "whitewash", "retirement",
    "retired", "champions", "trophy", "series win", "decisive", "upset",
    "innings and", "announcement", "bcci", "icc", "test championship"
}

ROUTINE_SCORECARD_PATTERNS = [
    "live score", "ball-by-ball", "ball by ball", "scorecard", "playing xi",
    "toss update", "innings break", "lunch update", "tea update", "day 1:",
    "day 2:", "day 3:", "day 4:", "stumps", "overs", "runs for"
]

GEOPOLITICS_HIGH_IMPACT = {
    "treaty", "sanctions", "strike", "ceasefire", "summit", "bilateral",
    "border", "india", "modi", "security council", "united nations", "defense", "missile",
    "diplomatic", "agreement", "pact", "escalation", "conflict", "election"
}

AI_HIGH_IMPACT = {
    "breakthrough", "benchmark", "open-source", "open-weight", "weights",
    "reasoning", "frontier", "architecture", "arxiv", "inference", "agent",
    "transformer", "fine-tuning", "safety", "context length", "state-of-the-art"
}


class NewsRanker:
    """Computes multi-factor explainable ranking score for clustered news stories."""

    def __init__(self):
        self.settings = get_settings()

    def calculate_recency_score(self, published_at: datetime) -> float:
        """Calculate exponential decay recency score."""
        if not published_at:
            return 0.50
        now = datetime.now(timezone.utc)
        diff_hours = max((now - published_at).total_seconds() / 3600.0, 0.0)
        # Half-life around 72 hours with floor of 0.35
        return max(math.exp(-diff_hours / 72.0), 0.35)

    def calculate_source_quality_score(self, source_name: str) -> float:
        """Assign trust weight based on editorial classification."""
        s = source_name.lower()
        if any(official in s for official in ("icc", "arxiv", "united nations", "un news", "mea")):
            return 1.00
        if any(high in s for high in ("bbc", "reuters", "the hindu", "espncricinfo", "wisden", "hugging face", "mit technology")):
            return 0.85
        return 0.65

    def calculate_domain_impact(self, article: NormalizedArticle) -> Tuple[float, float, str]:
        """Calculate domain relevance, impact score, and rationale."""
        text = f"{article.title} {article.short_description}".lower()
        domain = article.category.lower()

        relevance = 0.50
        impact = 0.50
        rationale = "Standard development"

        if domain == "cricket":
            # Check routine scorecard exclusion
            for pat in ROUTINE_SCORECARD_PATTERNS:
                if pat in text:
                    return 0.0, 0.0, "Disqualified as routine match scorecard / live update"

            impact_matches = [w for w in CRICKET_HIGH_IMPACT if w in text]
            if impact_matches:
                relevance = 0.90
                impact = min(0.60 + len(impact_matches) * 0.12, 1.0)
                rationale = f"Significant cricket milestone detected ({', '.join(impact_matches[:3])})"
            else:
                relevance = 0.60
                impact = 0.40
                rationale = "Standard match or cricket news report"

        elif domain == "geopolitics":
            impact_matches = [w for w in GEOPOLITICS_HIGH_IMPACT if re.search(rf"\b{re.escape(w)}\b", text)]
            if re.search(r"\b(india|delhi)\b", text):
                relevance = 0.95
                impact = min(0.65 + len(impact_matches) * 0.10, 1.0)
                rationale = "High strategic relevance involving India and foreign policy"
            elif impact_matches:
                relevance = 0.85
                impact = min(0.55 + len(impact_matches) * 0.10, 1.0)
                rationale = f"Major international diplomatic/security development ({', '.join(impact_matches[:3])})"
            else:
                relevance = 0.35
                impact = 0.25
                rationale = "Routine local or non-strategic report"

        elif domain == "ai_news":
            if article.paper_data is not None:
                relevance = 0.95
                impact = 0.80
                rationale = f"Peer-reviewed / pre-print research paper on arXiv ({article.paper_data.arxiv_id})"
            else:
                impact_matches = [w for w in AI_HIGH_IMPACT if w in text]
                if impact_matches:
                    relevance = 0.90
                    impact = min(0.60 + len(impact_matches) * 0.10, 1.0)
                    rationale = f"Significant AI development ({', '.join(impact_matches[:3])})"
                else:
                    relevance = 0.65
                    impact = 0.50
                    rationale = "AI industry news"

        return relevance, impact, rationale

    def rank_cluster(self, cluster: StoryCluster) -> NormalizedArticle:
        """Compute composite score for the cluster's primary article."""
        art = cluster.primary_article

        relevance, impact, rationale = self.calculate_domain_impact(art)
        recency = self.calculate_recency_score(art.published_at) if art.published_at else 0.5
        src_quality = self.calculate_source_quality_score(art.source_name)

        # Corroboration based on cluster size
        c_size = cluster.cluster_size
        corrob = 0.50 if c_size == 1 else (0.80 if c_size == 2 else 1.00)

        # Composite score calculation
        if relevance == 0.0 and impact == 0.0:
            composite = 0.0
        else:
            composite = (
                self.settings.WEIGHT_RELEVANCE * relevance +
                self.settings.WEIGHT_IMPACT * impact +
                self.settings.WEIGHT_RECENCY * recency +
                self.settings.WEIGHT_SOURCE_QUALITY * src_quality +
                self.settings.WEIGHT_CORROBORATION * corrob
            )

        art.importance_score = round(composite, 3)
        art.recency_score = round(recency, 3)
        art.source_quality_score = round(src_quality, 3)
        art.ranking_explanation = (
            f"Score: {art.importance_score} (Impact={impact:.2f}, Recency={recency:.2f}, "
            f"Quality={src_quality:.2f}, Corroboration={corrob:.2f}) | {rationale}"
        )

        return art

    def rank_and_sort(self, clusters: List[StoryCluster], max_count: int = 5) -> List[NormalizedArticle]:
        """Rank all clusters and return top qualifying stories up to max_count."""
        ranked_articles = [self.rank_cluster(c) for c in clusters]
        # Filter out routine scorecards and low quality stories (threshold 0.35)
        qualified = [a for a in ranked_articles if a.importance_score >= 0.35]
        # Sort descending by importance score
        qualified.sort(key=lambda a: a.importance_score, reverse=True)
        return qualified[:max_count]
