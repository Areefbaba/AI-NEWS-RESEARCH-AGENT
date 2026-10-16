"""Input validation guardrails: Query sanitization and boundary checks."""

import re
from typing import Optional, Tuple

PROHIBITED_DOMAINS = {"football", "soccer", "nfl", "nba", "mlb"}
ALLOWED_DOMAINS = {"cricket", "geopolitics", "ai_news"}


def validate_domain_input(domain: str) -> Tuple[bool, str]:
    """Validate domain against allowed list and prohibited list."""
    if not domain:
        return False, "Domain cannot be empty."

    d = domain.strip().lower()
    if d in PROHIBITED_DOMAINS:
        return False, f"Prohibited domain: {domain} is strictly excluded."

    if d not in ALLOWED_DOMAINS:
        return False, f"Unsupported domain: {domain}. Must be one of: {', '.join(sorted(ALLOWED_DOMAINS))}."

    return True, "Valid domain."


def sanitize_query(query: Optional[str], max_len: int = 120) -> str:
    """Sanitize user input search query to prevent script injection and buffer issues."""
    if not query:
        return ""

    # Truncate length
    clean = query.strip()[:max_len]

    # Remove dangerous HTML/Script tags and contents
    clean = re.sub(r"<script.*?>.*?</script>", "", clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r"<style.*?>.*?</style>", "", clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r"<[^>]*>", "", clean)

    # Remove non-printable or dangerous control chars
    clean = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", clean)

    # Normalize whitespace
    clean = " ".join(clean.split())
    return clean
