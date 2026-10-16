"""Unit tests for article normalization and URL cleaning."""

from datetime import datetime, timezone
import pytest
from app.schemas.article import RawArticle
from app.services.normalization import clean_canonical_url, parse_datetime_safe, normalize_raw_article


def test_clean_canonical_url_strips_tracking():
    dirty = "https://www.espncricinfo.com/story/test-match?utm_source=twitter&utm_medium=social&fbclid=12345&id=99#"
    cleaned = clean_canonical_url(dirty)
    assert "utm_source" not in cleaned
    assert "fbclid" not in cleaned
    assert "id=99" in cleaned
    assert cleaned.startswith("https://www.espncricinfo.com/story/test-match")


def test_parse_datetime_safe():
    # RFC 822 format (RSS)
    rfc_date = "Mon, 12 Oct 2026 04:30:00 +0000"
    dt = parse_datetime_safe(rfc_date)
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.day == 12

    # ISO format
    iso_date = "2026-10-12T14:20:00Z"
    dt_iso = parse_datetime_safe(iso_date)
    assert dt_iso is not None
    assert dt_iso.hour == 14

    # Invalid date returns None without crashing
    assert parse_datetime_safe("Not a date") is None
    assert parse_datetime_safe(None) is None


def test_normalize_raw_article_full():
    raw = RawArticle(
        source_id="reuters_world",
        source_name="Reuters",
        source_domain="reuters.com",
        url="https://reuters.com/world/article-1?utm_medium=feed",
        title="<b>Major Diplomatic Summit</b> Concludes in Geneva",
        summary_raw="<p>Leaders sign new accords on international trade and sanctions.</p>",
        published_raw="2026-10-11T10:00:00Z",
        extra_metadata={"subcategories": "diplomacy,global_conflicts"}
    )

    norm = normalize_raw_article(raw, default_domain="geopolitics")
    assert norm.title == "Major Diplomatic Summit Concludes in Geneva"
    assert "utm_medium" not in norm.canonical_url
    assert "accord" in norm.short_description
    assert norm.category == "geopolitics"
    assert norm.subcategory == "diplomacy"
    assert norm.published_at is not None
    assert len(norm.content_fingerprint) == 64
