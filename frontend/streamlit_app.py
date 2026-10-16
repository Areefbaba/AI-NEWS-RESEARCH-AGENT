"""Production Streamlit user interface for the AI News & Research Agent."""

import os
import sys
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

# Ensure root workspace directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.graph.workflow import run_research_workflow
from app.services.llm import get_llm_manager

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI News & Research Agent",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN PRODUCTION CSS (DARK & LIGHT THEME ADAPTIVE) ---
st.markdown("""
<style>
    /* Global Container Adjustments */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3.5rem;
    }

    /* Main Branding Header */
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.3rem;
        background: linear-gradient(90deg, #3B82F6, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-bottom: 1.6rem;
        font-weight: 400;
        line-height: 1.5;
    }

    /* Production Modern Card Container */
    .news-card-box {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }

    /* Adaptive Badges (No clash in dark or light mode) */
    .badge {
        display: inline-block;
        padding: 0.28rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 600;
        border-radius: 6px;
        margin-right: 0.5rem;
        margin-bottom: 0.4rem;
        letter-spacing: 0.01em;
    }
    .badge-primary {
        background-color: rgba(59, 130, 246, 0.15);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .badge-success {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-warning {
        background-color: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .badge-secondary {
        background-color: rgba(148, 163, 184, 0.15);
        color: #CBD5E1;
        border: 1px solid rgba(148, 163, 184, 0.3);
    }

    /* Translucent Adaptive Callout Boxes (Eliminates blinding white rect) */
    .callout-box {
        background-color: rgba(59, 130, 246, 0.07);
        border-left: 4px solid #3B82F6;
        border-radius: 0 8px 8px 0;
        padding: 0.9rem 1.1rem;
        margin: 0.9rem 0;
        color: inherit;
        line-height: 1.55;
    }
    .india-box {
        background-color: rgba(245, 158, 11, 0.08);
        border-left: 4px solid #F59E0B;
        border-radius: 0 8px 8px 0;
        padding: 0.9rem 1.1rem;
        margin: 0.9rem 0;
        color: inherit;
        line-height: 1.55;
    }

    .summary-text {
        font-size: 0.97rem;
        line-height: 1.68;
        margin-top: 0.8rem;
        margin-bottom: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)


def render_card_table(card):
    """Render clean full-width structured data table for a news card without charts."""
    if card.table_data:
        st.markdown("**📋 Key Structured Data**")
        df_table = pd.DataFrame(card.table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)


# --- PRODUCTION SIDEBAR: INTELLIGENCE CONTROLS (NO TELEMETRY / HEALTH MONITOR) ---
with st.sidebar:
    st.subheader("🎛️ Intelligence Engine")

    llm_mgr = get_llm_manager()
    provider_id, provider_name, model_info = llm_mgr.get_preferred_engine_status()

    if provider_id in ("groq", "gemini", "openai"):
        st.success(f"🟢 **Active Engine**: {provider_name}")
        st.caption(f"⚡ {model_info}")
    elif provider_id == "ollama":
        st.success(f"🟢 **Active Engine**: {provider_name}")
        st.caption(f"🖥️ {model_info}")
    else:
        st.info("⚡ **Active Engine**: Heuristic Analyzer")
        st.caption("Zero Token Cost / Deterministic Verification Mode")

    with st.expander("Model Fallback Pipeline", expanded=False):
        st.markdown(
            "1. **Groq** (`llama-3.3-70b-versatile`)\n"
            "2. **Google Gemini** (`gemini-1.5-flash`)\n"
            "3. **OpenAI** (`gpt-4o-mini`)\n"
            "4. **Local Ollama** (`qwen2.5:7b`)\n"
            "5. **Deterministic Heuristic** (Offline Fallback)"
        )
        st.caption("Cascading fallback ensures uninterrupted operation when API tokens or rate limits exhaust.")

    st.markdown("---")
    st.subheader("🔍 Retrieval Controls")
    time_window = st.slider("Freshness Window (Hours)", min_value=12, max_value=168, value=48, step=12)
    force_refresh = st.button("🔄 Force Refresh Live Feeds", use_container_width=True)

    st.markdown("---")
    st.caption("AI News & Research Agent v1.1.0 | Production Edition")
    st.caption("✓ Strict Evidence Policy | ✓ Zero Hallucinations")


# --- MAIN HEADER ---
st.markdown('<div class="main-title">📡 AI News & Research Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Multi-source verified intelligence across Cricket, Geopolitics, and AI Research. No rumors, no routine scorecards, no hallucinations.</div>', unsafe_allow_html=True)


# --- EXACTLY THREE MAIN NAVIGATION TABS ---
# (Football is strictly excluded per project requirements)
tab_cricket, tab_geopolitics, tab_ai = st.tabs([
    "🏏 Cricket News",
    "🌍 Geopolitics",
    "🤖 AI News & Research"
])


# ==============================================================================
# 1. CRICKET NEWS SCREEN
# ==============================================================================
with tab_cricket:
    st.subheader("Cricket Intelligence")
    st.caption("Historic milestones, decisive Test outcomes, international match analysis, and confirmed player announcements. Routine scorecards strictly filtered.")

    # Four designated subcategories
    cricket_cat = st.radio(
        "Cricket Category Filter",
        options=["Major Cricket News", "Test Cricket", "International Match Updates", "Major Player Updates"],
        horizontal=True
    )

    cat_mapping = {
        "Major Cricket News": "major_cricket",
        "Test Cricket": "test_cricket",
        "International Match Updates": "international_matches",
        "Major Player Updates": "player_updates"
    }
    selected_subcat = cat_mapping[cricket_cat]

    with st.spinner("Analyzing verified cricket sources..."):
        briefing = run_research_workflow(
            domain="cricket",
            category_filter=selected_subcat,
            time_window_hours=time_window,
            bypass_cache=force_refresh
        )

    # Status Bar
    cache_badge = "⚡ Cached Briefing" if briefing.is_cached else "🌐 Live Discovery"
    st.caption(f"{cache_badge} | Generated: {briefing.generated_at.strftime('%Y-%m-%d %H:%M UTC')} | Evaluated {briefing.total_articles_evaluated} articles across {briefing.total_sources_scanned} sources")

    if briefing.notice_message:
        st.info(briefing.notice_message)

    if not briefing.cards:
        st.warning(f"No qualifying stories currently meet the strict significance threshold for {cricket_cat}. Ordinary match scorecards are excluded.")
    else:
        for card in briefing.cards:
            with st.container():
                st.markdown(f"### [{card.headline}]({card.canonical_url})")

                # Badges
                st.markdown(f"""
                <span class="badge badge-primary">{card.subcategory.replace('_', ' ').title()}</span>
                <span class="badge badge-secondary">{card.source_name}</span>
                <span class="badge {'badge-success' if card.verification_status == 'verified' else 'badge-warning'}">
                    {'✓ Confirmed' if card.is_confirmed_announcement else '⚠ Unconfirmed Speculation'}
                </span>
                <span style="font-size: 0.85rem; color: #94A3B8;">Published: {card.published_date}</span>
                """, unsafe_allow_html=True)

                # ~200-Word Analytical Summary
                st.markdown(f'<div class="summary-text">{card.summary}</div>', unsafe_allow_html=True)

                # Why It Matters Callout
                st.markdown(f"""
                <div class="callout-box">
                    <strong>Why It Matters:</strong> {card.why_it_matters}
                </div>
                """, unsafe_allow_html=True)

                # Structured Key Data Table (Charts removed for clean UI)
                render_card_table(card)

                if card.uncertainty_caveats:
                    st.caption(f"ℹ️ **Caveat**: {card.uncertainty_caveats}")

                # Supporting Sources Expander
                if card.supporting_citations:
                    with st.expander(f"Original Sources & Evidence ({len(card.supporting_citations)})"):
                        for cit in card.supporting_citations:
                            st.markdown(f"- [{cit.title}]({cit.url}) — *{cit.source_name}*")
                st.markdown("---")


# ==============================================================================
# 2. GEOPOLITICS SCREEN
# ==============================================================================
with tab_geopolitics:
    st.subheader("Geopolitics & Strategic Intelligence")
    st.caption("Top qualifying high-impact global developments ranked by significance, strategic impact, and source corroboration (Max 5 stories).")

    geo_filter = st.selectbox(
        "Focus Filter",
        options=["All High-Impact Stories", "India Strategic & Bilateral", "Global Security & Conflicts"],
        index=0
    )

    with st.spinner("Analyzing geopolitical dispatches and foreign policy records..."):
        briefing = run_research_workflow(
            domain="geopolitics",
            time_window_hours=time_window,
            bypass_cache=force_refresh
        )

    cache_badge = "⚡ Cached Briefing" if briefing.is_cached else "🌐 Live Discovery"
    st.caption(f"{cache_badge} | Generated: {briefing.generated_at.strftime('%Y-%m-%d %H:%M UTC')} | Evaluated {briefing.total_articles_evaluated} dispatches across {briefing.total_sources_scanned} sources")

    if briefing.notice_message:
        st.info(briefing.notice_message)

    # Filter cards if requested
    cards = briefing.cards
    if geo_filter == "India Strategic & Bilateral":
        cards = [c for c in cards if c.india_implications is not None]
    elif geo_filter == "Global Security & Conflicts":
        cards = [c for c in cards if c.india_implications is None]

    if not cards:
        st.warning("No geopolitical stories currently meet the evidence and relevance requirements for this filter.")
    else:
        for idx, card in enumerate(cards, 1):
            with st.container():
                st.markdown(f"### {idx}. [{card.headline}]({card.canonical_url})")

                # Metadata Badges
                st.markdown(f"""
                <span class="badge badge-primary">Actors: {card.actors_involved or 'International'}</span>
                <span class="badge badge-secondary">{card.source_name}</span>
                <span class="badge {'badge-success' if card.verification_status == 'verified' else 'badge-warning'}">
                    {'✓ Verified Fact' if card.verification_status == 'verified' else '⚠ Official Statement / Allegation'}
                </span>
                <span style="font-size: 0.85rem; color: #94A3B8;">Published: {card.published_date}</span>
                """, unsafe_allow_html=True)

                # ~200-Word Analytical Summary
                st.markdown(f'<div class="summary-text">{card.summary}</div>', unsafe_allow_html=True)

                # India Implications Callout
                if card.india_implications:
                    st.markdown(f"""
                    <div class="india-box">
                        <strong>🇮🇳 Strategic Implications for India:</strong><br>{card.india_implications}
                    </div>
                    """, unsafe_allow_html=True)

                # Global Implications Callout
                if card.global_implications:
                    st.markdown(f"""
                    <div class="callout-box">
                        <strong>🌐 Broader International Implications:</strong><br>{card.global_implications}
                    </div>
                    """, unsafe_allow_html=True)

                # Structured Key Data Table (Charts removed for clean UI)
                render_card_table(card)

                if card.uncertainty_caveats:
                    st.caption(f"⚖️ **Evidence & Uncertainty**: {card.uncertainty_caveats}")

                if card.supporting_citations:
                    with st.expander(f"Original Sources & Evidence ({len(card.supporting_citations)})"):
                        for cit in card.supporting_citations:
                            st.markdown(f"- [{cit.title}]({cit.url}) — *{cit.source_name}*")
                st.markdown("---")


# ==============================================================================
# 3. AI NEWS & RESEARCH SCREEN
# ==============================================================================
with tab_ai:
    st.subheader("AI News & Research")
    st.caption("Frontier arXiv research papers, official foundation model launches, and high-impact infrastructure developments.")

    ai_cat = st.radio(
        "Category",
        options=["All AI Developments", "New Research Papers (arXiv)", "Newly Launched Models", "Major AI Industry Developments"],
        horizontal=True
    )

    with st.spinner("Querying arXiv API and AI lab release feeds..."):
        briefing = run_research_workflow(
            domain="ai_news",
            time_window_hours=time_window,
            bypass_cache=force_refresh
        )

    cache_badge = "⚡ Cached Briefing" if briefing.is_cached else "🌐 Live Discovery"
    st.caption(f"{cache_badge} | Generated: {briefing.generated_at.strftime('%Y-%m-%d %H:%M UTC')} | Evaluated {briefing.total_articles_evaluated} items across {briefing.total_sources_scanned} sources")

    if briefing.notice_message:
        st.info(briefing.notice_message)

    # Filter cards
    cards = briefing.cards
    if ai_cat == "New Research Papers (arXiv)":
        cards = [c for c in cards if c.subcategory == "research_papers"]
    elif ai_cat == "Newly Launched Models":
        cards = [c for c in cards if c.subcategory == "model_launches"]
    elif ai_cat == "Major AI Industry Developments":
        cards = [c for c in cards if c.subcategory == "industry_developments"]

    if not cards:
        st.warning(f"No qualifying stories currently meet the evidence and quality thresholds for {ai_cat}.")
    else:
        for card in cards:
            with st.container():
                st.markdown(f"### [{card.headline}]({card.canonical_url})")

                # Research Paper Layout
                if card.subcategory == "research_papers":
                    st.markdown(f"""
                    <span class="badge badge-primary">arXiv Pre-print</span>
                    <span class="badge badge-secondary">Authors: {', '.join(card.authors[:3]) if card.authors else 'Listed on arXiv'}</span>
                    <span style="font-size: 0.85rem; color: #94A3B8;">Published: {card.published_date}</span>
                    """, unsafe_allow_html=True)

                    st.markdown(f'<div class="summary-text">{card.summary}</div>', unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="callout-box">
                        <strong>Why An AI Engineer Should Care:</strong><br>{card.why_it_matters}
                    </div>
                    """, unsafe_allow_html=True)

                    # Structured Key Data Table (Charts removed for clean UI)
                    render_card_table(card)

                    with st.expander("🔬 Technical Deep-Dive & Findings", expanded=False):
                        st.markdown(f"**Research Problem**: {card.research_problem}")
                        st.markdown(f"**Proposed Method**: {card.proposed_method}")
                        st.markdown(f"**Reported Findings**: {card.main_findings}")
                        st.markdown(f"**Known Limitations**: {card.limitations}")
                        st.markdown(f"**Practical Takeaways**: {card.engineer_takeaways}")
                        if card.code_url:
                            st.markdown(f"📄 [Download Official arXiv PDF]({card.code_url})")

                # Model Launch Layout
                elif card.subcategory == "model_launches":
                    st.markdown(f"""
                    <span class="badge badge-primary">Model Launch</span>
                    <span class="badge badge-secondary">{card.developer or 'AI Lab'}</span>
                    <span class="badge {'badge-success' if card.is_open_weights else 'badge-warning'}">
                        {card.license_status or 'Commercial'}
                    </span>
                    <span style="font-size: 0.85rem; color: #94A3B8;">Released: {card.published_date}</span>
                    """, unsafe_allow_html=True)

                    st.markdown(f'<div class="summary-text">{card.summary}</div>', unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="callout-box">
                        <strong>Ecosystem Impact:</strong><br>{card.why_it_matters}
                    </div>
                    """, unsafe_allow_html=True)

                    # Structured Key Data Table (Charts removed for clean UI)
                    render_card_table(card)

                # Industry Development Layout
                else:
                    st.markdown(f"""
                    <span class="badge badge-primary">Industry News</span>
                    <span class="badge badge-secondary">{card.source_name}</span>
                    <span style="font-size: 0.85rem; color: #94A3B8;">Published: {card.published_date}</span>
                    """, unsafe_allow_html=True)

                    st.markdown(f'<div class="summary-text">{card.summary}</div>', unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="callout-box">
                        <strong>Why It Matters:</strong> {card.why_it_matters}
                    </div>
                    """, unsafe_allow_html=True)

                    # Structured Key Data Table (Charts removed for clean UI)
                    render_card_table(card)

                if card.uncertainty_caveats:
                    st.caption(f"ℹ️ **Evaluation Note**: {card.uncertainty_caveats}")

                if card.supporting_citations:
                    with st.expander(f"Original Paper / Evidence Links ({len(card.supporting_citations)})"):
                        for cit in card.supporting_citations:
                            st.markdown(f"- [{cit.title}]({cit.url}) — *{cit.source_name}*")
                st.markdown("---")
