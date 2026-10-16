"""Article and paper normalization, URL sanitization, date parsing, and fingerprinting."""

import hashlib
import re
import urllib.parse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from dateutil import parser as dateutil_parser

from app.schemas.article import NormalizedArticle, RawArticle, ExtractedPaper
from app.sources.article_extractor import clean_html_text

# Tracking query parameters to strip
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "ref", "ref_src", "_ga", "ocid", "cid"
}


def clean_canonical_url(url_str: str) -> str:
    """Strip marketing query params and standardize URL representation."""
    if not url_str:
        return ""
    try:
        parsed = urllib.parse.urlparse(url_str.strip())
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        cleaned_pairs = [(k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS]
        clean_query = urllib.parse.urlencode(cleaned_pairs)
        # Standardize path: remove trailing slash if not root
        path = parsed.path
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]
        rebuilt = urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            parsed.params,
            clean_query,
            ""  # drop fragment
        ))
        return rebuilt
    except Exception:
        return url_str.strip()


def parse_datetime_safe(date_str: Optional[str]) -> Optional[datetime]:
    """Parse various RSS/Atom/ISO datetime formats into timezone-aware UTC datetime."""
    if not date_str:
        return None
    date_str = date_str.strip()
    # 1. Try RFC-2822 standard email/RSS date
    try:
        dt = parsedate_to_datetime(date_str)
        if dt:
            return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # 2. Try ISO 8601
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # 3. Fallback to dateutil parser
    try:
        dt = dateutil_parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    return None


def compute_content_fingerprint(title: str, text: str) -> str:
    """Generate deterministic SHA-256 content fingerprint for deduplication."""
    norm_title = re.sub(r"[^\w\s]", "", title.lower())
    norm_title = " ".join(norm_title.split())
    norm_text = re.sub(r"[^\w\s]", "", text[:300].lower())
    norm_text = " ".join(norm_text.split())
    payload = f"{norm_title}::{norm_text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalize_raw_article(raw: RawArticle, default_domain: str = "ai_news") -> NormalizedArticle:
    """Convert RawArticle into validated NormalizedArticle."""
    canonical_url = clean_canonical_url(raw.url)
    clean_title = clean_html_text(raw.title)
    clean_desc = clean_html_text(raw.summary_raw or "")
    clean_body = clean_html_text(raw.content_raw or raw.summary_raw or "")
    fingerprint = compute_content_fingerprint(clean_title, clean_body)
    article_id = f"art_{fingerprint[:14]}"

    published_dt = parse_datetime_safe(raw.published_raw)

    # Determine subcategory and domain
    subcats = raw.extra_metadata.get("subcategories", "").split(",")
    primary_subcat = subcats[0].strip() if subcats and subcats[0].strip() else None

    # Handle research paper structure
    paper_data: Optional[ExtractedPaper] = None
    if raw.extra_metadata.get("is_paper") == "true":
        arxiv_id = raw.extra_metadata.get("arxiv_id", "")
        authors_list = [a.strip() for a in raw.extra_metadata.get("authors", "").split(",") if a.strip()]
        paper_data = ExtractedPaper(
            arxiv_id=arxiv_id,
            title=clean_title,
            authors=authors_list,
            published_date=published_dt or datetime.now(timezone.utc),
            abstract=clean_desc or clean_body,
            primary_category=raw.extra_metadata.get("primary_category", "cs.AI"),
            pdf_url=raw.extra_metadata.get("pdf_url", f"https://arxiv.org/pdf/{arxiv_id}.pdf"),
            abs_url=canonical_url,
            is_revision=raw.extra_metadata.get("is_revision", "false").lower() == "true",
            research_problem=f"Addressed in paper: {clean_title}",
            proposed_method="Detailed in experimental paper evaluation.",
            main_findings="Primary findings published in arXiv pre-print abstract.",
            limitations="Formal limitations specified in complete technical report.",
            engineer_takeaways="Check arXiv PDF for reproduction code and benchmarks."
        )

    return NormalizedArticle(
        id=article_id,
        title=clean_title,
        canonical_url=canonical_url,
        source_name=raw.source_name,
        source_domain=raw.source_domain,
        published_at=published_dt,
        retrieved_at=raw.retrieved_at,
        category=default_domain,
        subcategory=primary_subcat,
        short_description=clean_desc[:350],
        extracted_content_or_excerpt=clean_body[:2500],
        content_fingerprint=fingerprint,
        verification_status="verified" if raw.source_name in ("ICC", "arXiv", "The Hindu", "Reuters", "BBC") else "unconfirmed",
        paper_data=paper_data
    )
