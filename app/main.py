import argparse
import os
import sys
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.graph.workflow import run_research_workflow
from app.services.llm import get_analysis_mode

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ai_news_agent")


def main():
    parser = argparse.ArgumentParser(description="AI News & Research Agent CLI")
    parser.add_argument(
        "--domain",
        type=str,
        default="ai_news",
        choices=["cricket", "geopolitics", "ai_news"],
        help="Target domain to fetch and analyze"
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Subcategory filter (e.g., test_cricket, research_papers)"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=48,
        help="Time window in hours"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Bypass cache and force fresh retrieval"
    )

    args = parser.parse_args()

    mode, _ = get_analysis_mode()
    print("=" * 70)
    print(f"AI NEWS & RESEARCH AGENT - DOMAIN: {args.domain.upper()}")
    print(f"Analysis Engine Mode: {mode.upper()}")
    print("=" * 70)

    briefing = run_research_workflow(
        domain=args.domain,
        category_filter=args.category,
        time_window_hours=args.hours,
        bypass_cache=args.refresh
    )

    if briefing.notice_message:
        print(f"\n[NOTICE]: {briefing.notice_message}\n")

    print(f"Total stories discovered: {len(briefing.cards)}")
    for idx, card in enumerate(briefing.cards, 1):
        print(f"\n[{idx}] {card.headline}")
        print(f"    Source: {card.source_name} | Published: {card.published_date}")
        print(f"    URL: {card.canonical_url}")
        print(f"    Summary: {card.summary}")
        print(f"    Why It Matters: {card.why_it_matters}")
        if card.india_implications:
            print(f"    India Impact: {card.india_implications}")
        if card.paper_title:
            print(f"    arXiv Paper: {card.paper_title} (Authors: {', '.join(card.authors[:3])})")


if __name__ == "__main__":
    main()
