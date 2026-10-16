# Product Requirements Document (PRD)
# AI News & Research Agent

## 1. Product Vision & Overview
The **AI News & Research Agent** is a dedicated, production-minded intelligence application designed to discover, verify, score, synthesize, and present critical current developments across three strictly defined domains:
1. **Cricket News** (Major records/outcomes, Test cricket, International match decisive updates, Major player developments)
2. **Geopolitics** (Major conflict/security shifts, leadership & policy changes, diplomatic treaties/sanctions, India foreign relations & strategic developments, global stability impacts)
3. **AI News & Research** (Peer-reviewed arXiv papers, frontier/open-weight model launches, key industry & infrastructure milestones)

The agent moves beyond generic chatbots and naive RSS aggregators:
- Discovers information from verifiable primary and established secondary sources.
- Ranks developments using an explainable, multi-factor significance score.
- Rigorously filters out routine sports scorecards, uncorroborated rumors, duplicate wire stories, and marketing noise.
- Provides grounded, cited summaries detailing **what happened**, **why it matters**, **India/global impact**, and **uncertainty/verification caveats**.
- Preserves genuine canonical URLs and timestamps.
- Integrates optional local LLM analysis via Ollama (Qwen) with complete graceful fallback when offline.

---

## 2. Problem Statement & User Personas
### 2.1 Problem
- **Information Overload & Noise**: Mainstream news is flooded with clickbait, routine cricket ball-by-ball scorecards, superficial marketing press releases, and duplicate syndications.
- **Hallucinations & Disinformation**: AI chatbots frequently hallucinate paper citations, sports margins, diplomatic statements, and dates.
- **Lack of Impact Analysis**: Existing aggregators provide headlines without explaining *why* a development matters to an engineer, researcher, or geopolitical observer.

### 2.2 Target Users
1. **AI Researchers & Engineers**: Want substantive research papers (arXiv) and verified open-weight/proprietary model launches without promotional hype.
2. **Geopolitical Analysts & Informed Observers**: Require balanced, evidence-backed geopolitical updates distinguishing confirmed facts from official allegations, with specific attention to India's strategic interests.
3. **Cricket Aficionados**: Seek historic milestones, decisive Test match results, upset analysis, and confirmed player retirements, explicitly excluding routine match commentary and scorecards.

---

## 3. Product Scope & Explicit Exclusions
### 3.1 In-Scope Domains
- **Cricket News**:
  - *Category 1*: Major Cricket News (Historic margin victories, tournament decisive stages, world records, major board decisions).
  - *Category 2*: Test Cricket News (Decisive Test outcomes, series milestones, historic red-ball records).
  - *Category 3*: Important International Match Updates (Major upsets, decisive tournament qualification/elimination, historic spells/innings).
  - *Category 4*: Major Player Updates (Official retirement announcements by format, career comebacks, confirmed international availability).
- **Geopolitics**:
  - Top 5 qualifying stories ranked by significance, recency, source quality, and impact.
  - Core breakdown: What happened, actors involved, confirmed vs. uncertain, India implications, global implications, original citations.
- **AI News & Research**:
  - *Category 1*: New Research Papers (arXiv LLM/RAG/Agents/Reasoning papers with methodology, findings, limitations, engineer takeaways).
  - *Category 2*: Newly Launched Models (Verified releases, license status, context length, developer, benchmarks if corroborated).
  - *Category 3*: Major AI Industry Developments (Core infrastructure, open-source frameworks, regulatory/safety milestones).

### 3.2 Explicit Exclusions
- **NO Football (Soccer) News**: Explicitly prohibited from the application.
- **NO Routine Cricket Scorecards or Ball-by-ball Feeds**: Live commentary and ordinary domestic match reports are filtered out.
- **NO Fabricated or Hallucinated News**: If fewer than 5 stories meet quality thresholds, display fewer. Never invent stories to fill slots.
- **NO Unverifiable Social Media Rumors**: Speculative posts or unconfirmed transfers/retirements are flagged or excluded.

---

## 4. Freshness, Sources, and Citation Rules
1. **Freshness Windows**:
   - Default configurable window: 24 to 72 hours for breaking news and research papers.
   - Historical records or background context must be explicitly distinguished from current event dates.
2. **Source Registry**:
   - Verified RSS endpoints, official organizational releases (BCCI, ICC, UN, MEA, arXiv API), and high-trust independent journalism (Reuters, BBC, The Hindu, ESPNcricinfo, Wisden, TechCrunch, arXiv).
   - Each source maintains a trust classification (`HIGH`, `MEDIUM`, `OFFICIAL`).
3. **Citations & Provenance**:
   - Every claim is tied to canonical source URLs.
   - Preserves source name, publication timestamp, and retrieved excerpt.
   - Direct clickable links rendered in Streamlit.

---

## 5. Functional Requirements
- **FR-1: Multi-domain Ingestion**: Parallel or asynchronous retrieval from registered RSS feeds and arXiv API without blocking the UI.
- **FR-2: Content Normalization & URL Validation**: Validate URLs (reject localhost/SSRF/malformed URLs), parse standard dates, and generate deterministic content fingerprints (`content_fingerprint`).
- **FR-3: Deduplication & Clustering**: Group related reports covering the same event using title/content cosine similarity and token overlaps, preserving all supporting citations while electing the highest-quality primary canonical link.
- **FR-4: Domain Classification & Policy Filtering**:
  - Cricket policy filters out ordinary matches (< historical threshold) and speculative gossip.
  - Geopolitics policy ensures high-impact ranking and extracts India-relevance.
  - AI policy validates paper submissions vs revisions and verifies official model release links.
- **FR-5: Multi-Factor Importance Ranking**:
  $$\text{Score} = w_{\text{rel}} \cdot S_{\text{rel}} + w_{\text{impact}} \cdot S_{\text{impact}} + w_{\text{rec}} \cdot S_{\text{rec}} + w_{\text{src}} \cdot S_{\text{src}} + w_{\text{corrob}} \cdot S_{\text{corrob}}$$
- **FR-6: LangGraph Orchestration**: Declarative StateGraph linking ingestion, normalization, filtering, ranking, analysis, and verification.
- **FR-7: Dual-Mode Summarization**:
  - *Local LLM Mode*: Uses Ollama with Qwen (e.g. `qwen2.5:7b` or configurable) for deep structured extraction.
  - *Heuristic Fallback Mode*: If Ollama is offline or model is missing, gracefully extract lead claims, key sentences, and metadata without crashing or hallucinating.
- **FR-8: Streamlit UI**:
  - Interactive tabs for Cricket, Geopolitics, and AI News & Research.
  - Real-time refresh button, cache status indicator, source health indicators, time filters.
  - Interactive cards with collapsible technical details, India impact analysis, and direct source links.

---

## 6. Non-Functional Requirements
- **Performance**: Workflow completion under 10 seconds for cached or heuristic passes; under 30 seconds with local LLM.
- **Reliability & Resilience**: Feed failures or HTTP timeouts must be caught, logged, and isolated. The overall app must never crash on network failure.
- **Security & Guardrails**:
  - SSRF protection against private IP ranges (`127.0.0.1`, `169.254.169.254`, `10.0.0.0/8`, etc.).
  - Input sanitization against prompt injection.
  - Strict separation of untrusted web content from system prompts.
- **Zero Paid API Cost**: Base application operates entirely with free public feeds, arXiv, and local Ollama. Optional web search interfaces support API keys if supplied.

---

## 7. Acceptance Criteria
- [x] Three main sections (Cricket, Geopolitics, AI) cleanly exposed; NO football section.
- [x] Cricket separates 4 specific categories and rejects routine scorecards.
- [x] Geopolitics presents top $\le 5$ validated stories with India implications and uncertainty notes.
- [x] AI section provides research papers (arXiv), model launches, and industry updates.
- [x] System operates seamlessly with or without local Ollama running.
- [x] Test suite covers unit, integration, guardrails, ranking, and deduplication with $>85\%$ coverage.
