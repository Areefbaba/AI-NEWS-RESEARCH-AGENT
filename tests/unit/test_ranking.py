"""Unit tests for multi-factor news ranking."""

from datetime import datetime, timezone, timedelta
import pytest
from app.schemas.article import NormalizedArticle
from app.services.deduplication import StoryCluster
from app.services.news_ranker import NewsRanker


def create_article(title, category, source_name="Reuters", hours_ago=2):
    published = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return NormalizedArticle(
        id=f"art_{hash(title) % 100000}",
        title=title,
        canonical_url=f"https://example.com/{hash(title)}",
        source_name=source_name,
        source_domain="example.com",
        published_at=published,
        category=category,
        short_description=f"Summary of {title}",
        extracted_content_or_excerpt="Full excerpt content",
        content_fingerprint=f"fp_{hash(title)}"
    )


def test_cricket_routine_scorecard_penalized():
    ranker = NewsRanker()

    routine_art = create_article("Ranji Trophy Day 2: Mumbai 250/4 vs Delhi, live score updates", "cricket")
    routine_cluster = StoryCluster(cluster_id="c1", primary_article=routine_art)
    ranked_routine = ranker.rank_cluster(routine_cluster)

    historic_art = create_article("India achieve historic clean sweep in Test series against England", "cricket", "ICC")
    historic_cluster = StoryCluster(cluster_id="c2", primary_article=historic_art)
    ranked_historic = ranker.rank_cluster(historic_cluster)

    assert ranked_routine.importance_score < 0.35, "Routine scorecard should be scored below inclusion threshold"
    assert ranked_historic.importance_score > 0.70, "Historic Test clean sweep should score highly"


def test_geopolitics_india_relevance_boost():
    ranker = NewsRanker()

    generic_art = create_article("Local municipal election concludes in small European township", "geopolitics")
    india_art = create_article("India and France sign landmark defense pact and strategic agreement", "geopolitics", "The Hindu")

    c1 = StoryCluster(cluster_id="c1", primary_article=generic_art)
    c2 = StoryCluster(cluster_id="c2", primary_article=india_art)

    r1 = ranker.rank_cluster(c1)
    r2 = ranker.rank_cluster(c2)

    assert r2.importance_score > r1.importance_score
    assert "India" in r2.ranking_explanation


def test_ranking_sort_and_threshold():
    ranker = NewsRanker()

    articles = [
        create_article("Live score ball-by-ball update", "cricket"),
        create_article("Toss update: Team chooses to bat first", "cricket"),
        create_article("India win historic Test match by 250 runs to claim World Championship", "cricket", "ICC"),
    ]
    clusters = [StoryCluster(cluster_id=f"c_{i}", primary_article=a) for i, a in enumerate(articles)]

    qualified = ranker.rank_and_sort(clusters, max_count=5)
    # The two routine updates must be filtered out by threshold
    assert len(qualified) == 1
    assert "historic Test match" in qualified[0].title
