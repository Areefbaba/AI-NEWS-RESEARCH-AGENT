"""Unit tests for story deduplication and clustering."""

from datetime import datetime, timezone
import pytest
from app.schemas.article import NormalizedArticle
from app.services.deduplication import cluster_and_deduplicate, tokenize_title, calculate_token_similarity


def create_mock_article(id_str, title, source_name, url):
    return NormalizedArticle(
        id=id_str,
        title=title,
        canonical_url=url,
        source_name=source_name,
        source_domain="example.com",
        published_at=datetime.now(timezone.utc),
        category="cricket",
        short_description="Match report",
        extracted_content_or_excerpt="Long detailed match content of significant length...",
        content_fingerprint=f"fp_{id_str}"
    )


def test_token_similarity():
    t1 = tokenize_title("India defeat Australia by 200 runs in historic final")
    t2 = tokenize_title("India crush Australia by 200 runs to seal championship")
    sim = calculate_token_similarity(t1, t2)
    assert sim >= 0.40

    t3 = tokenize_title("New quantum computing breakthrough in silicon")
    assert calculate_token_similarity(t1, t3) == 0.0


def test_cluster_and_deduplicate_merges_same_event():
    art1 = create_mock_article(
        "art_1",
        "India crush Australia by 200 runs in historic Test final",
        "ESPNcricinfo",
        "https://cricinfo.com/story1"
    )
    art2 = create_mock_article(
        "art_2",
        "India defeat Australia by 200 runs to clinch Test championship",
        "BBC Sport Cricket",
        "https://bbc.com/sport/cricket/story2"
    )
    art3 = create_mock_article(
        "art_3",
        "Star batter announces retirement from international cricket",
        "ICC Cricket News",
        "https://icc-cricket.com/retire"
    )

    clusters = cluster_and_deduplicate([art1, art2, art3])
    # Expect 2 clusters: one for the 200-run match, one for the retirement
    assert len(clusters) == 2

    # Find the match cluster
    match_cluster = next(c for c in clusters if "200 runs" in c.primary_article.title)
    assert match_cluster.cluster_size == 2
    assert len(match_cluster.primary_article.supporting_sources) == 1
    assert match_cluster.primary_article.supporting_sources[0]["url"] in ("https://cricinfo.com/story1", "https://bbc.com/sport/cricket/story2")
