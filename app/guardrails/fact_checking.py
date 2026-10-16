"""Fact-checking and citation integrity guardrails."""

from typing import List, Tuple
from app.schemas.briefing import NewsCard


def verify_citation_integrity(card: NewsCard) -> Tuple[bool, List[str]]:
    """Verify that a card has verifiable supporting citations with real URLs."""
    issues = []

    if not card.canonical_url or not card.canonical_url.startswith("http"):
        issues.append(f"Card '{card.headline}' missing valid canonical URL.")

    if not card.supporting_citations:
        issues.append(f"Card '{card.headline}' has zero supporting citations.")
    else:
        for idx, cit in enumerate(card.supporting_citations):
            if not cit.url or not cit.url.startswith("http"):
                issues.append(f"Citation {idx} for '{card.headline}' has invalid URL: {cit.url}")

    return len(issues) == 0, issues
