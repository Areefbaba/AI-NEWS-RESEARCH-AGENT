import os
import sys
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.graph.workflow import run_research_workflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("scheduler")


def run_daily_briefings():
    """Execute pipeline for all 3 supported domains and persist to cache."""
    domains = ["cricket", "geopolitics", "ai_news"]
    logger.info("Starting automated daily briefing pipeline for domains: %s", domains)

    results = {}
    for dom in domains:
        try:
            logger.info("Executing research workflow for domain: %s", dom)
            briefing = run_research_workflow(domain=dom, time_window_hours=48, bypass_cache=True)
            results[dom] = len(briefing.cards)
            logger.info("Successfully refreshed %s briefing: %d cards generated.", dom, len(briefing.cards))
        except Exception as e:
            logger.error("Error refreshing domain %s: %s", dom, e)

    logger.info("Daily briefings update completed. Results summary: %s", results)
    return results


if __name__ == "__main__":
    run_daily_briefings()
