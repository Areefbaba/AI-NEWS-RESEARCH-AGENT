"""Evaluation test suite: Evaluates news ranking quality, factuality, and threshold filtering."""

import json
from datetime import datetime, timezone
import pytest
from app.schemas.article import NormalizedArticle
from app.services.deduplication import StoryCluster
from app.services.news_ranker import NewsRanker


@pytest.fixture
def benchmark_stories():
    """Labeled benchmark test cases for ranking evaluation."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": "eval_geo_high",
            "title": "India and France sign historic defense treaty on strategic border deterrence",
            "category": "geopolitics",
            "source_name": "The Hindu",
            "expected_top": True,
            "min_score": 0.70
        },
        {
            "id": "eval_geo_routine",
            "title": "Local municipal council holds routine budget meeting in small county",
            "category": "geopolitics",
            "source_name": "Local Wire",
            "expected_top": False,
            "max_score": 0.60
        },
        {
            "id": "eval_cricket_historic",
            "title": "India crush Australia by an innings and 222 runs in record Test series victory",
            "category": "cricket",
            "source_name": "ESPNcricinfo",
            "expected_top": True,
            "min_score": 0.70
        },
        {
            "id": "eval_cricket_routine",
            "title": "Ranji Trophy Day 2: Mumbai 140/3 vs Baroda, live scorecard and ball by ball",
            "category": "cricket",
            "source_name": "Local Sports",
            "expected_top": False,
            "max_score": 0.30
        },
    ]


def test_ranking_evaluation_benchmark(benchmark_stories):
    ranker = NewsRanker()
    now = datetime.now(timezone.utc)

    for item in benchmark_stories:
        art = NormalizedArticle(
            id=item["id"],
            title=item["title"],
            canonical_url=f"https://example.com/{item['id']}",
            source_name=item["source_name"],
            source_domain="example.com",
            published_at=now,
            category=item["category"],
            short_description=item["title"],
            extracted_content_or_excerpt=item["title"],
            content_fingerprint=f"fp_{item['id']}"
        )
        cluster = StoryCluster(cluster_id=f"c_{item['id']}", primary_article=art)
        ranked = ranker.rank_cluster(cluster)

        if "min_score" in item:
            assert ranked.importance_score >= item["min_score"], (
                f"Story '{item['title']}' scored {ranked.importance_score}, expected >= {item['min_score']}"
            )

        if "max_score" in item:
            assert ranked.importance_score <= item["max_score"], (
                f"Story '{item['title']}' scored {ranked.importance_score}, expected <= {item['max_score']}"
            )
