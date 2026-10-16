"""Source definitions, RSS feeds, and official arXiv API client for AI News & Research."""

import time
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional
import httpx

from app.config import get_settings
from app.schemas.article import RawArticle, ExtractedPaper
from app.schemas.source import SourceConfig, TrustLevel, SourceType, NewsDomain, SourceHealth
from app.sources.base import BaseSourceAdapter
from app.storage.repository import ArticleRepository

logger = logging.getLogger(__name__)

# Atom namespace used by arXiv
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivSourceAdapter(BaseSourceAdapter):
    """Adapter for official arXiv REST/Atom API."""

    def __init__(self, repo: Optional[ArticleRepository] = None):
        super().__init__(repo)
        self.settings = get_settings()

    def fetch(self, config: SourceConfig) -> List[RawArticle]:
        """Fetch latest computer science AI/LLM/Agents research papers from arXiv."""
        start_time = time.time()
        articles: List[RawArticle] = []
        status = "healthy"
        error_msg: Optional[str] = None
        latency_ms: float = 0.0

        query_url = config.url
        cached_content = self.repo.get_feed_cache(query_url)
        xml_content = cached_content

        if not xml_content:
            try:
                headers = {"User-Agent": self.settings.USER_AGENT}
                with httpx.Client(timeout=config.timeout_seconds, follow_redirects=True, headers=headers) as client:
                    response = client.get(query_url)
                    latency_ms = (time.time() - start_time) * 1000

                    if response.status_code == 200:
                        xml_content = response.text
                        self.repo.set_feed_cache(query_url, xml_content, ttl_hours=self.settings.CACHE_TTL_HOURS)
                    else:
                        status = "degraded"
                        error_msg = f"HTTP {response.status_code}: {response.reason_phrase}"
            except Exception as e:
                status = "failing"
                error_msg = str(e)
                logger.warning("arXiv fetch failed: %s", e)

        if xml_content:
            try:
                root = ET.fromstring(xml_content)
                entries = root.findall("atom:entry", ATOM_NS)
                for entry in entries:
                    raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
                    title = entry.findtext("atom:title", default="", namespaces=ATOM_NS).strip()
                    title = " ".join(title.split())  # normalize internal line breaks
                    summary = entry.findtext("atom:summary", default="", namespaces=ATOM_NS).strip()
                    published_str = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
                    updated_str = entry.findtext("atom:updated", default="", namespaces=ATOM_NS)

                    # Extract authors
                    author_elements = entry.findall("atom:author/atom:name", ATOM_NS)
                    authors = [a.text.strip() for a in author_elements if a.text]

                    # Detect primary category
                    primary_cat = ""
                    cat_elem = entry.find("arxiv:primary_category", ATOM_NS)
                    if cat_elem is not None:
                        primary_cat = cat_elem.attrib.get("term", "")

                    # Extract links
                    abs_url = raw_id
                    pdf_url = ""
                    for link in entry.findall("atom:link", ATOM_NS):
                        if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                            pdf_url = link.attrib.get("href", "")
                        elif link.attrib.get("rel") == "alternate":
                            abs_url = link.attrib.get("href", raw_id)

                    is_revision = False
                    if published_str and updated_str and updated_str != published_str:
                        is_revision = True

                    # Extract arXiv clean identifier
                    arxiv_id = abs_url.split("/abs/")[-1] if "/abs/" in abs_url else abs_url

                    article = RawArticle(
                        source_id=config.source_id,
                        source_name="arXiv",
                        source_domain="arxiv.org",
                        url=abs_url,
                        title=title,
                        summary_raw=summary,
                        content_raw=summary,
                        author=", ".join(authors[:5]) if authors else None,
                        published_raw=published_str,
                        retrieved_at=datetime.now(timezone.utc),
                        extra_metadata={
                            "arxiv_id": arxiv_id,
                            "pdf_url": pdf_url,
                            "primary_category": primary_cat,
                            "authors": ", ".join(authors),
                            "is_revision": str(is_revision),
                            "is_paper": "true"
                        }
                    )
                    articles.append(article)

            except Exception as e:
                status = "degraded"
                error_msg = f"Failed to parse arXiv Atom XML: {e}"
                logger.error(error_msg)

        health = SourceHealth(
            source_id=config.source_id,
            name=config.name,
            status=status,
            last_attempt=datetime.now(timezone.utc),
            last_success=datetime.now(timezone.utc) if status == "healthy" else None,
            error_message=error_msg,
            latency_ms=latency_ms if latency_ms > 0 else None,
            items_fetched=len(articles)
        )
        self.repo.update_source_health(health)
        return articles


def get_ai_sources() -> List[SourceConfig]:
    """Return verified public sources for AI News & Research."""
    return [
        SourceConfig(
            source_id="arxiv_ai_recent",
            name="arXiv AI & Computation",
            url="http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=15",
            domain="arxiv.org",
            trust_level=TrustLevel.OFFICIAL,
            source_type=SourceType.API,
            news_domains=[NewsDomain.AI_NEWS],
            subcategories=["research_papers"],
            priority=1,
            trust_rationale="Primary pre-print repository for frontier machine learning research."
        ),
        SourceConfig(
            source_id="huggingface_daily_papers",
            name="Hugging Face Daily Papers",
            url="https://papers.huggingface.co/rss",
            domain="huggingface.co",
            trust_level=TrustLevel.HIGH,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.AI_NEWS],
            subcategories=["research_papers", "model_launches"],
            priority=1,
            trust_rationale="Curated community discussion and daily trending peer research."
        ),
        SourceConfig(
            source_id="mit_tech_review_ai",
            name="MIT Technology Review AI",
            url="https://www.technologyreview.com/feed/",
            domain="technologyreview.com",
            trust_level=TrustLevel.HIGH,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.AI_NEWS],
            subcategories=["industry_developments", "model_launches"],
            priority=2,
            trust_rationale="Academic journalism analyzing practical impact of AI breakthroughs."
        ),
        SourceConfig(
            source_id="ai_news_feed",
            name="Artificial Intelligence News",
            url="https://www.artificialintelligence-news.com/feed/",
            domain="artificialintelligence-news.com",
            trust_level=TrustLevel.MEDIUM,
            source_type=SourceType.RSS,
            news_domains=[NewsDomain.AI_NEWS],
            subcategories=["industry_developments", "model_launches"],
            priority=2,
            trust_rationale="Covers commercial releases, developer tooling, and enterprise AI."
        ),
    ]
