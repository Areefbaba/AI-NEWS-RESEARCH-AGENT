# Project Memory & Development Journal
# AI News & Research Agent

## 1. Project Context & Objectives
- **System**: Production-grade AI News & Research Agent with three dedicated sections:
  1. Cricket News (Major news, Test cricket, International matches, Major player updates)
  2. Geopolitics (Top 5 high-impact stories with India & global implications)
  3. AI News & Research (New arXiv papers, Model launches, Industry developments)
- **Primary Tech Stack**: Python 3.14, LangGraph, Streamlit, Pydantic, SQLite, httpx, feedparser, BeautifulSoup4, Ollama/Qwen (with robust heuristic fallback).
- **Core Product Rule**: No fabricated news, no football news, no routine cricket scorecards, mandatory original clickable links, complete offline degradation when Ollama is unavailable.

---

## 2. Architectural Decisions & Conventions
1. **Decision**: Explicit Separation of Intelligence and Heuristic Extraction.
   - *Rationale*: If Ollama is offline or the user does not have a local GPU, the system must degrade gracefully to a structured heuristic extractor rather than failing or inventing mock news.
2. **Decision**: LangGraph TypedDict State.
   - *Rationale*: Keeps graph states transparent, testable, and strictly typed with Pydantic schemas serialized across nodes.
3. **Decision**: Multi-Factor Scoring with Explainable Weights.
   - *Rationale*: Users and analysts require transparent explanations of why a story was ranked top 5 rather than an opaque black-box rank.
4. **Decision**: SQLite for Caching & Persistence.
   - *Rationale*: Embedded, zero external database dependency, supports TTL caching to avoid refetching stale feeds continuously.
5. **Decision**: Strict SSRF & Injection Guardrails.
   - *Rationale*: Crawling and analyzing arbitrary RSS/article content requires defense against private IP scanning, local metadata endpoints, and embedded LLM instructions.

---

## 3. Implementation Status & Journal
- **2026-10-12 (Phases 0 through 9 Completed)**:
  - **Environment**: Python 3.14.5 on Windows, Streamlit 1.63, LangGraph 1.2.7, Pydantic 2.13.4, SQLite 3.
  - **Documentation**: All 6 core documents created and maintained (`PRD.md`, `DESIGN.md`, `EVALUATION.md`, `RULES.md`, `TASKS.md`, `MEMORY.md`).
  - **Storage & Caching**: SQLite repository (`Database`, `ArticleRepository`) implemented with WAL mode, persistent `:memory:` support for unit tests, TTL caching for feeds and briefings.
  - **Sources Layer**: `SourceRegistry` holding 13 verified feeds across Cricket, Geopolitics, and AI Research. `ArxivSourceAdapter` (Atom REST client), `RSSReaderAdapter` (with `feedparser`), and `WebSearchProvider` interface.
  - **Normalization & Deduplication**: Canonical URL sanitization (stripping tracking query parameters), robust UTC date parsing, SHA-256 content fingerprinting, and token Jaccard similarity clustering (`StoryCluster`).
  - **Ranking Engine**: Explainable multi-factor scoring with transparent weights. Rigorously penalizes routine cricket scorecards (score clamped to 0.0), elevates historic records/Test victories, promotes strategic India foreign policy dispatches, and tracks arXiv papers.
  - **Domain Agents**:
    - `CricketDomainAgent`: Filters routine ball-by-ball commentary, classifies into 4 tabs (Major, Test, International Matches, Player Updates), and distinguishes confirmed announcements from rumors.
    - `GeopoliticsDomainAgent`: Limits stories to top 5, extracts key geopolitical actors, separates official allegations from verified dispatches, and analyzes strategic implications for India without inventing connections.
    - `AINewsDomainAgent`: Classifies into arXiv Research Papers (with problem, method, findings, limitations, takeaways), Model Launches (developer, open-weight status), and Industry Developments.
  - **Guardrails**: Input query sanitization (blocking `<script>` and control chars), SSRF tool guardrail (blocking `127.0.0.1`, RFC 1918 private IPs, `169.254.169.254`, and non-HTTP schemes), prompt injection defenses (neutralizing `[INST]` and jailbreak tokens), and output secret redaction.
  - **Orchestration**: `create_news_graph()` StateGraph in LangGraph linking request validation, cache check, source collection, normalization, deduplication, ranking, report generation, and output guardrails.
  - **Intelligence Engine**: Ollama client dynamically tests `http://localhost:11434/api/tags`. When Ollama is offline or model `qwen2.5:7b` is not pulled, automatically activates `HeuristicAnalyzer` for lead excerpt synthesis without hallucinations.
  - **UI**: Interactive multi-tab Streamlit dashboard (`frontend/streamlit_app.py`) featuring exactly 3 sections (Cricket, Geopolitics, AI News), sidebar telemetry, source health indicators, and direct clickable citations.
  - **Verification**: Complete pytest suite executed: **42 passed, 0 failures, 79% overall code coverage**.

---

## 4. Observed Test Results & Live Telemetry
- `pytest -v`: 42 passed in 1.09s across `tests/unit`, `tests/integration`, `tests/guardrails`, and `tests/evaluation`.
- Live CLI run `python app/main.py --domain ai_news --refresh`: Discovered and structured 5 real arXiv papers (`2610.12467v1`, `2610.12466v1`, etc.) with authors, abstracts, and PDF links.
- Live CLI run `python app/main.py --domain cricket --refresh`: Discovered 10 major cricket developments (record partnerships, BCCI decisions, world record runs, Test catch records) while successfully excluding routine match scorecards.
- Live CLI run `python app/main.py --domain geopolitics --refresh`: Discovered top 5 qualifying dispatches with India foreign policy implications and official statement caveats.
- Endpoint resilience: Handled 404 responses from `icc-cricket.com/rss/news` and `news.un.org` gracefully, marking them degraded in `SourceHealth` while completing the pipeline with remaining active feeds.

---

## 5. Known Limitations & Recommendations
1. **Local Ollama Model**: While Ollama is running, the model `qwen2.5:7b` must be pulled via `ollama pull qwen2.5:7b` for local neural synthesis. In the interim, Heuristic Fallback mode provides 100% verified source excerpts.
2. **External Feeds**: A few third-party RSS endpoints occasionally change URL formats or return 404/403. The source registry is easily updated in `app/sources/`.

---

## 6. Next Steps for Continuing Development
1. Start Streamlit UI: `streamlit run frontend/streamlit_app.py`.
2. Optional: Run `ollama pull qwen2.5:7b` to activate local neural analysis.
3. Configure optional search API key in `.env` if internet-wide search is desired.
