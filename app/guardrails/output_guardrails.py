"""Output validation guardrails: Secret leak prevention and final card validation."""

import re
from typing import List, Tuple
from app.schemas.briefing import NewsBriefing, NewsCard
from app.guardrails.fact_checking import verify_citation_integrity

SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{20,}",
    r"tvly-[a-zA-Z0-9]{20,}",
    r"api[_-]?key[_-]?[a-zA-Z0-9]{16,}",
    r"password\s*=\s*['\"][^'\"]+['\"]"
]


def redact_secrets_from_text(text: str) -> str:
    """Scrub potential leaked secrets or API keys from output text."""
    if not text:
        return ""
    clean = text
    for pat in SECRET_PATTERNS:
        clean = re.sub(pat, "[REDACTED_SECRET]", clean, flags=re.IGNORECASE)
    return clean


def validate_output_briefing(briefing: NewsBriefing) -> Tuple[NewsBriefing, List[str]]:
    """Validate all cards in a briefing, ensuring citation validity and scrubbing secrets."""
    audit_warnings = []
    clean_cards: List[NewsCard] = []

    for card in briefing.cards:
        # 1. Fact checking citation audit
        is_valid_cit, cit_issues = verify_citation_integrity(card)
        if not is_valid_cit:
            audit_warnings.extend(cit_issues)
            # Retain card but mark verification status as degraded
            card.verification_status = "unconfirmed"
            card.uncertainty_caveats = "Incomplete citation provenance."

        # 2. Secret leak scrubber
        card.headline = redact_secrets_from_text(card.headline)
        card.summary = redact_secrets_from_text(card.summary)
        card.why_it_matters = redact_secrets_from_text(card.why_it_matters)
        if card.what_happened:
            card.what_happened = redact_secrets_from_text(card.what_happened)
        if card.india_implications:
            card.india_implications = redact_secrets_from_text(card.india_implications)

        clean_cards.append(card)

    briefing.cards = clean_cards
    return briefing, audit_warnings
