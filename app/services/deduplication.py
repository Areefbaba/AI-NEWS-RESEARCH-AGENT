"""Story deduplication, clustering, and canonical election."""

import re
from typing import Dict, List, Set
from pydantic import BaseModel, Field

from app.schemas.article import NormalizedArticle

# Common stop words to exclude from title similarity
STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "up", "about", "into", "over", "after", "is", "are", "was",
    "were", "be", "been", "has", "have", "had", "do", "does", "did", "as", "it"
}


class StoryCluster(BaseModel):
    """Cluster of articles reporting on the identical core news event."""
    cluster_id: str
    primary_article: NormalizedArticle
    supporting_articles: List[NormalizedArticle] = Field(default_factory=list)

    @property
    def cluster_size(self) -> int:
        return 1 + len(self.supporting_articles)


def tokenize_title(title: str) -> Set[str]:
    """Extract significant lowercase word tokens from title."""
    words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", title.lower())
    return {w for w in words if w not in STOP_WORDS}


def calculate_token_similarity(tokens1: Set[str], tokens2: Set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    return intersection / union if union > 0 else 0.0


def score_primary_candidate(art: NormalizedArticle) -> float:
    """Evaluate article quality for canonical election within a cluster."""
    score = 0.0
    # Prefer official / high quality sources
    if art.source_name in ("ICC", "arXiv", "UN News Global Perspective"):
        score += 3.0
    elif art.source_name in ("The Hindu", "BBC World News", "ESPNcricinfo"):
        score += 2.0
    else:
        score += 1.0

    # Content completeness
    content_len = len(art.extracted_content_or_excerpt or "")
    score += min(content_len / 1000.0, 2.0)

    # Presence of timestamp
    if art.published_at is not None:
        score += 0.5

    return score


def cluster_and_deduplicate(
    articles: List[NormalizedArticle],
    similarity_threshold: float = 0.38
) -> List[StoryCluster]:
    """Group duplicate articles into StoryClusters and elect the best primary article."""
    if not articles:
        return []

    clusters: List[StoryCluster] = []

    for article in articles:
        tokens = tokenize_title(article.title)
        matched_cluster = None

        # Check existing clusters
        for cluster in clusters:
            primary_tokens = tokenize_title(cluster.primary_article.title)
            sim = calculate_token_similarity(tokens, primary_tokens)

            # Also check exact fingerprint match
            if article.content_fingerprint == cluster.primary_article.content_fingerprint or sim >= similarity_threshold:
                matched_cluster = cluster
                break

        if matched_cluster:
            # Check if this new article should become primary
            curr_score = score_primary_candidate(matched_cluster.primary_article)
            new_score = score_primary_candidate(article)

            if new_score > curr_score:
                # Demote old primary to supporting, make new article primary
                old_primary = matched_cluster.primary_article
                matched_cluster.primary_article = article
                matched_cluster.supporting_articles.append(old_primary)
            else:
                matched_cluster.supporting_articles.append(article)
        else:
            # Create a new cluster
            new_cluster = StoryCluster(
                cluster_id=f"cluster_{article.id}",
                primary_article=article,
                supporting_articles=[]
            )
            clusters.append(new_cluster)

    # Attach supporting source links to each primary article
    for cluster in clusters:
        citations = []
        for sup in cluster.supporting_articles:
            citations.append({
                "title": sup.title,
                "url": sup.canonical_url,
                "source_name": sup.source_name,
                "published_date": sup.published_at.isoformat() if sup.published_at else None
            })
        cluster.primary_article.supporting_sources = citations

    return clusters
