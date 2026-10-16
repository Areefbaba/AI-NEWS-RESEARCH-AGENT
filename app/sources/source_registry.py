"""Centralized Source Registry for registering and querying verified news and research feeds."""

import logging
from typing import Dict, List, Optional
from app.schemas.source import SourceConfig, NewsDomain
from app.sources.cricket_sources import get_cricket_sources
from app.sources.geopolitics_sources import get_geopolitics_sources
from app.sources.ai_research_sources import get_ai_sources

logger = logging.getLogger(__name__)


class SourceRegistry:
    """Registry maintaining configurations and metadata for all authorized sources."""

    def __init__(self):
        self._sources: Dict[str, SourceConfig] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default trusted sources for all 3 supported domains."""
        # Cricket sources
        for src in get_cricket_sources():
            self.register_source(src)

        # Geopolitics sources
        for src in get_geopolitics_sources():
            self.register_source(src)

        # AI News & Research sources
        for src in get_ai_sources():
            self.register_source(src)

        logger.info("SourceRegistry initialized with %d verified sources.", len(self._sources))

    def register_source(self, config: SourceConfig) -> None:
        """Register or update a source configuration."""
        self._sources[config.source_id] = config

    def get_source_by_id(self, source_id: str) -> Optional[SourceConfig]:
        """Fetch a specific source by unique ID."""
        return self._sources.get(source_id)

    def get_all_sources(self) -> List[SourceConfig]:
        """Return all registered sources."""
        return list(self._sources.values())

    def get_sources_for_domain(self, domain: str, active_only: bool = True) -> List[SourceConfig]:
        """Retrieve sources configured for a specific news domain."""
        matched = []
        domain_str = domain.lower()
        for src in self._sources.values():
            if active_only and not src.is_active:
                continue
            for d in src.news_domains:
                if d.value == domain_str:
                    matched.append(src)
                    break
        # Sort by priority ascending (1 = highest)
        matched.sort(key=lambda s: s.priority)
        return matched


_default_registry: Optional[SourceRegistry] = None


def get_default_source_registry() -> SourceRegistry:
    """Singleton getter for default source registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = SourceRegistry()
    return _default_registry
