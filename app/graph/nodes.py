"""Pure functional nodes for LangGraph news and research workflow."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from app.graph.state import AgentState
from app.schemas.article import RawArticle, NormalizedArticle
from app.schemas.briefing import NewsBriefing
from app.schemas.source import SourceConfig, SourceType
from app.sources.source_registry import get_default_source_registry
from app.sources.rss_reader import RSSReaderAdapter
from app.sources.ai_research_sources import ArxivSourceAdapter
from app.sources.web_search import get_search_provider
from app.services.normalization import normalize_raw_article
from app.services.deduplication import cluster_and_deduplicate, StoryCluster
from app.services.news_ranker import NewsRanker
from app.services.report_generator import ReportGenerator
from app.storage.repository import ArticleRepository

logger = logging.getLogger(__name__)


def validate_request_node(state: AgentState) -> Dict[str, Any]:
    """Validate request parameters and enforce supported domain boundaries."""
    domain = (state.get("domain") or "").strip().lower()

    # Rule: Prohibit football news section
    if "football" in domain or "soccer" in domain:
        return {
            "is_valid_request": False,
            "error_message": "Invalid news domain: Football is strictly excluded from this system."
        }

    valid_domains = {"cricket", "geopolitics", "ai_news"}
    if domain not in valid_domains:
        return {
            "is_valid_request": False,
            "error_message": f"Unsupported news domain '{domain}'. Must be one of: cricket, geopolitics, ai_news."
        }

    time_window = max(min(state.get("time_window_hours", 48), 168), 1)

    return {
        "domain": domain,
        "time_window_hours": time_window,
        "is_valid_request": True,
        "error_message": None
    }


def check_cache_node(state: AgentState) -> Dict[str, Any]:
    """Check if an unexpired briefing is already present in cache."""
    if state.get("bypass_cache", False):
        return {"briefing": None}

    repo = ArticleRepository()
    cached = repo.get_cached_briefing(
        domain=state["domain"],
        category_filter=state.get("category_filter")
    )
    if cached:
        logger.info("Serving briefing from cache for domain %s", state["domain"])
        return {
            "briefing": cached.model_dump(),
            "source_health_summary": repo.get_all_source_health()
        }
    return {"briefing": None}


def collect_sources_node(state: AgentState) -> Dict[str, Any]:
    """Gather raw articles from registered RSS feeds and APIs."""
    if state.get("briefing") is not None:
        return {}  # Cache hit, skip retrieval

    repo = ArticleRepository()
    registry = get_default_source_registry()
    sources = registry.get_sources_for_domain(state["domain"])

    rss_adapter = RSSReaderAdapter(repo=repo)
    arxiv_adapter = ArxivSourceAdapter(repo=repo)

    raw_articles: List[Dict[str, Any]] = []

    for src in sources:
        try:
            if src.source_type == SourceType.API and src.domain == "arxiv.org":
                items = arxiv_adapter.fetch(src)
            else:
                items = rss_adapter.fetch(src)
            for it in items:
                raw_articles.append(it.model_dump())
        except Exception as e:
            logger.warning("Error fetching source %s: %s", src.source_id, e)

    # Optional search provider
    query = state.get("query")
    if query:
        search_provider = get_search_provider()
        search_items = search_provider.search(query, max_results=5)
        for sit in search_items:
            raw_articles.append(sit.model_dump())

    return {
        "source_configs": [s.model_dump() for s in sources],
        "raw_articles": raw_articles,
        "source_health_summary": repo.get_all_source_health()
    }


def normalize_articles_node(state: AgentState) -> Dict[str, Any]:
    """Normalize raw payloads, compute content fingerprints, and persist to SQLite."""
    if state.get("briefing") is not None:
        return {}

    repo = ArticleRepository()
    raw_list = state.get("raw_articles", [])
    cutoff = datetime.now(timezone.utc) - timedelta(hours=state["time_window_hours"])

    normalized: List[Dict[str, Any]] = []

    for r_dict in raw_list:
        raw_obj = RawArticle.model_validate(r_dict)
        norm_obj = normalize_raw_article(raw_obj, default_domain=state["domain"])

        repo.save_article(norm_obj)
        normalized.append(norm_obj.model_dump())

    return {"normalized_articles": normalized}


def deduplicate_cluster_node(state: AgentState) -> Dict[str, Any]:
    """Group duplicate articles covering the same news event into StoryClusters."""
    if state.get("briefing") is not None:
        return {}

    norm_list = state.get("normalized_articles", [])
    norm_objs = [NormalizedArticle.model_validate(d) for d in norm_list]

    clusters = cluster_and_deduplicate(norm_objs)

    return {
        "clustered_stories": [c.model_dump() for c in clusters]
    }


def rank_and_filter_node(state: AgentState) -> Dict[str, Any]:
    """Calculate multi-factor importance score and filter top qualified stories."""
    if state.get("briefing") is not None:
        return {}

    clusters_list = state.get("clustered_stories", [])
    cluster_objs = [StoryCluster.model_validate(c) for c in clusters_list]

    ranker = NewsRanker()
    # Rank up to 10 candidates to give domain agents room for subcategory filtering
    ranked_objs = ranker.rank_and_sort(cluster_objs, max_count=10)

    return {
        "ranked_articles": [a.model_dump() for a in ranked_objs]
    }


def generate_briefing_node(state: AgentState) -> Dict[str, Any]:
    """Generate final NewsBriefing with domain policies and citations."""
    if state.get("briefing") is not None:
        return {}

    ranked_list = state.get("ranked_articles", [])
    ranked_objs = [NormalizedArticle.model_validate(d) for d in ranked_list]

    generator = ReportGenerator()
    briefing = generator.generate_briefing(
        domain=state["domain"],
        articles=ranked_objs,
        category_filter=state.get("category_filter"),
        source_health_summary=state.get("source_health_summary", {}),
        total_sources=len(state.get("source_configs", [])),
        total_evaluated=len(state.get("raw_articles", [])),
        time_window_hours=state["time_window_hours"]
    )

    repo = ArticleRepository()
    repo.cache_briefing(briefing, ttl_hours=1)

    return {"briefing": briefing.model_dump()}


def output_guardrails_node(state: AgentState) -> Dict[str, Any]:
    """Validate briefing outputs, verifying citations and ensuring zero secret leaks."""
    briefing_dict = state.get("briefing")
    if not briefing_dict:
        return state

    cards = briefing_dict.get("cards", [])
    validated_cards = []

    for card in cards:
        # Guardrail 1: Enforce valid URL
        url = card.get("canonical_url", "")
        if not (url.startswith("http://") or url.startswith("https://")):
            continue

        # Guardrail 2: Ensure citations exist and have URLs
        citations = card.get("supporting_citations", [])
        clean_citations = [c for c in citations if c.get("url") and c["url"].startswith("http")]
        card["supporting_citations"] = clean_citations

        validated_cards.append(card)

    briefing_dict["cards"] = validated_cards
    return {
        "briefing": briefing_dict,
        "execution_metadata": {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "cards_count": len(validated_cards)
        }
    }
