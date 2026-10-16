"""Source definitions and feeds for Geopolitics."""

from typing import List
from app.schemas.source import SourceConfig, TrustLevel, SourceType, NewsDomain


def get_geopolitics_sources() -> List[SourceConfig]:
    """Return verified public sources for Geopolitics and Indian foreign policy."""
    return [
        SourceConfig(
            source_id="bbc_world",
            name="BBC World News",
            url="https://feeds.bbci.co.uk/news/world/rss.xml",
            domain="bbc.co.uk",
            trust_level=TrustLevel.HIGH,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.GEOPOLITICS],
            subcategories=["global_conflicts", "diplomacy", "governance"],
            priority=1,
            trust_rationale="Established international public news agency with verified reporting."
        ),
        SourceConfig(
            source_id="thehindu_international",
            name="The Hindu International",
            url="https://www.thehindu.com/news/international/feeder/default.rss",
            domain="thehindu.com",
            trust_level=TrustLevel.HIGH,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.GEOPOLITICS],
            subcategories=["diplomacy", "global_conflicts", "india_relations"],
            priority=1,
            trust_rationale="Major Indian national daily with extensive diplomatic and foreign affairs coverage."
        ),
        SourceConfig(
            source_id="thehindu_national",
            name="The Hindu National & Security",
            url="https://www.thehindu.com/news/national/feeder/default.rss",
            domain="thehindu.com",
            trust_level=TrustLevel.HIGH,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.GEOPOLITICS],
            subcategories=["india_relations", "defense_diplomacy"],
            priority=1,
            trust_rationale="Critical for Indian policy shifts, defense agreements, and border developments."
        ),
        SourceConfig(
            source_id="un_news_global",
            name="UN News Global Perspective",
            url="https://news.un.org/feed/subscribe/en/news/all/rss.xml",
            domain="news.un.org",
            trust_level=TrustLevel.OFFICIAL,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.GEOPOLITICS],
            subcategories=["diplomacy", "treaties", "global_stability"],
            priority=1,
            trust_rationale="Official United Nations communications service on international peace and sanctions."
        ),
        SourceConfig(
            source_id="aljazeera_world",
            name="Al Jazeera English",
            url="https://www.aljazeera.com/xml/rss/all.xml",
            domain="aljazeera.com",
            trust_level=TrustLevel.HIGH,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.GEOPOLITICS],
            subcategories=["global_conflicts", "diplomacy"],
            priority=2,
            trust_rationale="Global multi-regional news broadcaster covering Middle East, Asia, and international conflicts."
        ),
    ]
