"""Article extraction and HTML sanitization using BeautifulSoup."""

import re
import logging
from typing import Optional
from bs4 import BeautifulSoup
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# Patterns to strip out potential dangerous or injection tags
DANGEROUS_TAGS = ["script", "style", "iframe", "noscript", "svg", "button", "input", "form"]


def clean_html_text(html_content: str) -> str:
    """Extract clean, sanitized text from raw HTML content."""
    if not html_content:
        return ""

    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Decompose unsafe elements
        for tag in soup(DANGEROUS_TAGS):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception as e:
        logger.warning("HTML extraction failed, falling back to regex: %s", e)
        # Fallback regex tag stripping
        clean = re.sub(r"<[^>]+>", " ", html_content)
        return re.sub(r"\s+", " ", clean).strip()


def fetch_article_text(url: str, timeout_seconds: float = 8.0) -> Optional[str]:
    """Safely fetch and extract body text from an external article URL."""
    settings = get_settings()
    try:
        headers = {"User-Agent": settings.USER_AGENT}
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True, headers=headers) as client:
            response = client.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Decompose noise
                for noise in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                    noise.decompose()

                # Find main article container if available
                article_node = soup.find("article") or soup.find("main") or soup.find("body")
                if article_node:
                    paragraphs = article_node.find_all("p")
                    p_texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 25]
                    if p_texts:
                        return "\n\n".join(p_texts[:10])  # Top paragraphs
                    return clean_html_text(article_node.get_text())
                return clean_html_text(response.text)
    except Exception as e:
        logger.warning("Could not fetch article body from %s: %s", url, e)
    return None
