"""Base adapter class for data ingestion providers."""

from abc import ABC, abstractmethod
import logging
from typing import List, Optional
from app.schemas.article import RawArticle
from app.schemas.source import SourceConfig, SourceHealth
from app.storage.repository import ArticleRepository

logger = logging.getLogger(__name__)


class BaseSourceAdapter(ABC):
    """Abstract base class for all source ingestion adapters."""

    def __init__(self, repo: Optional[ArticleRepository] = None):
        self.repo = repo or ArticleRepository()

    @abstractmethod
    def fetch(self, config: SourceConfig) -> List[RawArticle]:
        """Fetch raw articles from the configured source endpoint.
        Must handle errors gracefully, record health status, and never crash caller.
        """
        pass
