"""Optional web search provider interface and implementations."""

from abc import ABC, abstractmethod
import logging
from typing import List, Optional
import httpx

from app.config import get_settings
from app.schemas.article import RawArticle

logger = logging.getLogger(__name__)


class WebSearchProvider(ABC):
    """Abstract interface for optional external web search providers."""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[RawArticle]:
        """Execute a web search query and return raw article hits."""
        pass


class NoOpSearchProvider(WebSearchProvider):
    """Default provider when no search API key is configured."""

    def search(self, query: str, max_results: int = 5) -> List[RawArticle]:
        logger.debug("No search provider active. Query '%s' skipped.", query)
        return []


class TavilySearchProvider(WebSearchProvider):
    """Tavily search provider when API key is provided."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://api.tavily.com/search"

    def search(self, query: str, max_results: int = 5) -> List[RawArticle]:
        results: List[RawArticle] = []
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": False
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(self.endpoint, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("results", []):
                        results.append(RawArticle(
                            source_id="tavily_search",
                            source_name="Web Search",
                            source_domain=httpx.URL(item.get("url", "")).host,
                            url=item.get("url", ""),
                            title=item.get("title", ""),
                            summary_raw=item.get("content", ""),
                            content_raw=item.get("content", ""),
                            extra_metadata={"score": str(item.get("score", 0.0))}
                        ))
        except Exception as e:
            logger.warning("Tavily search error for query '%s': %s", query, e)
        return results


def get_search_provider() -> WebSearchProvider:
    """Return configured search provider or NoOp fallback."""
    settings = get_settings()
    if settings.SEARCH_PROVIDER.lower() == "tavily" and settings.SEARCH_API_KEY:
        return TavilySearchProvider(api_key=settings.SEARCH_API_KEY)
    return NoOpSearchProvider()
