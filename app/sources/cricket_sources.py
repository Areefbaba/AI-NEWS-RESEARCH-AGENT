"""Source definitions and feeds for Cricket News."""

from typing import List
from app.schemas.source import SourceConfig, TrustLevel, SourceType, NewsDomain


def get_cricket_sources() -> List[SourceConfig]:
    """Return verified public sources for Cricket News."""
    return [
        SourceConfig(
            source_id="espncricinfo_global",
            name="ESPNcricinfo Global",
            url="https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
            domain="espncricinfo.com",
            trust_level=TrustLevel.HIGH,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.CRICKET],
            subcategories=["major_cricket", "test_cricket", "international_matches", "player_updates"],
            priority=1,
            trust_rationale="Leading global cricket journalism outlet with established editorial standards."
        ),
        SourceConfig(
            source_id="bbc_cricket",
            name="BBC Sport Cricket",
            url="https://feeds.bbci.co.uk/sport/cricket/rss.xml",
            domain="bbc.co.uk",
            trust_level=TrustLevel.HIGH,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.CRICKET],
            subcategories=["major_cricket", "test_cricket", "international_matches"],
            priority=2,
            trust_rationale="Major independent public broadcaster with rigorous verification."
        ),
        SourceConfig(
            source_id="ndtv_cricket",
            name="NDTV Cricket",
            url="https://feeds.feedburner.com/ndtvsports-cricket",
            domain="sports.ndtv.com",
            trust_level=TrustLevel.HIGH,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.CRICKET],
            subcategories=["major_cricket", "international_matches", "player_updates"],
            priority=2,
            trust_rationale="Dedicated Indian and international sports coverage."
        ),
        SourceConfig(
            source_id="icc_cricket_news",
            name="ICC Cricket News",
            url="https://www.icc-cricket.com/rss/news",
            domain="icc-cricket.com",
            trust_level=TrustLevel.OFFICIAL,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.CRICKET],
            subcategories=["major_cricket", "international_matches", "player_updates"],
            priority=1,
            trust_rationale="Official governing body for international cricket."
        ),
    ]
