# AI News & Research Agent

An intelligence research agent and interactive Streamlit application engineered to discover, score, verify, and summarize current developments across exactly three domains:
1. **Cricket News** (Major records & margin victories, Test cricket milestones, decisive international match updates, confirmed player announcements).
2. **Geopolitics** (High-impact security, diplomatic treaties, sanctions, and India's strategic foreign policy).
3. **AI News & Research** (Peer-reviewed arXiv papers, frontier & open-weight model launches, key infrastructure & tooling shifts).

> **Core Product Rule**: No fabricated news, no football news, no routine cricket scorecards, mandatory original clickable links, and transparent graceful fallback when local Ollama is offline.

---

## 1. Key Features & Architecture
- **Orchestration**: Orchestrated using **LangGraph** with a declarative `StateGraph` linking request validation, multi-source ingestion, canonical normalization, story clustering, multi-factor ranking, and citation guardrails.
- **Explainable Multi-Factor Ranking**:
  $$\text{Score} = w_{\text{rel}} \cdot S_{\text{rel}} + w_{\text{impact}} \cdot S_{\text{impact}} + w_{\text{rec}} \cdot S_{\text{rec}} + w_{\text{src}} \cdot S_{\text{src}} + w_{\text{corrob}} \cdot S_{\text{corrob}}$$
- **Dual Intelligence Engine**:
  - **Local Ollama (Qwen)**: Configurable local model (default: `qwen2.5:7b`) for structured semantic synthesis.
  - **Heuristic Fallback Engine**: If Ollama is offline or model is missing, degrades gracefully to deterministic, zero-hallucination lead excerpting without crashing or creating fake summaries.
- **Embedded Persistence**: SQLite repository with TTL caching for feeds and briefings to eliminate unnecessary external re-queries.
- **Zero Paid Dependencies**: Base application functions entirely with public feeds (ESPNcricinfo, BBC, The Hindu, arXiv API) and local Ollama. Optional search providers (e.g. Tavily) are pluggable via `.env`.

---

## 2. Project Structure
```
ai-news-research-agent/
│
├── app/
│   ├── main.py                  # CLI research workflow runner
│   ├── config.py                # Pydantic Settings & environment variables
│   ├── agents/
│   │   ├── cricket_agent.py     # Cricket subcategories & scorecard filtering
│   │   ├── geopolitics_agent.py # Geopolitics top-5 & India impact analysis
│   │   └── ai_news_agent.py     # arXiv papers & model launch classification
│   ├── graph/
│   │   ├── state.py             # LangGraph AgentState TypedDict
│   │   ├── nodes.py             # Functional pipeline nodes
│   │   ├── routing.py           # Conditional cache and validation routing
│   │   └── workflow.py          # StateGraph compilation & execution
│   ├── sources/
│   │   ├── base.py              # BaseSourceAdapter abstract base class
│   │   ├── source_registry.py   # Registry containing trusted feeds
│   │   ├── rss_reader.py        # Resilient RSS/Atom fetcher
│   │   ├── article_extractor.py # Safe BeautifulSoup HTML extractor
│   │   ├── cricket_sources.py   # Cricket feeds & endpoints
│   │   ├── geopolitics_sources.py # Geopolitics & Indian foreign policy feeds
│   │   ├── ai_research_sources.py # Official arXiv REST/Atom API adapter
│   │   └── web_search.py        # Pluggable external search provider
│   ├── services/
│   │   ├── llm.py               # Ollama client & heuristic fallback analyzer
│   │   ├── normalization.py     # URL cleaning & SHA-256 fingerprinting
│   │   ├── deduplication.py     # Story clustering & canonical election
│   │   ├── news_ranker.py       # Multi-factor explainable scoring engine
│   │   └── report_generator.py  # Structured briefing synthesizer
│   ├── guardrails/
│   │   ├── input_guardrails.py  # Query sanitization & boundary limits
│   │   ├── tool_guardrails.py   # SSRF defense (private IP & metadata block)
│   │   ├── prompt_injection.py  # Untrusted text instruction sanitizer
│   │   ├── fact_checking.py     # Citation provenance auditor
│   │   └── output_guardrails.py # Secret leak prevention
│   ├── schemas/
│   │   ├── article.py           # NormalizedArticle, RawArticle, ExtractedPaper
│   │   ├── source.py            # SourceConfig, SourceHealth, TrustLevel
│   │   └── briefing.py          # NewsCard, NewsBriefing, CitationLink
│   └── storage/
│       ├── database.py          # SQLite connection manager & schema migrations
│       └── repository.py        # Persistence & cache CRUD repository
│
├── frontend/
│   └── streamlit_app.py         # Multi-tab Streamlit dashboard
├── scheduler/
│   └── daily_briefing.py        # Background daily briefing pre-fetcher
├── docs/                        # PRD, DESIGN, EVALUATION, RULES, TASKS, MEMORY
├── tests/                       # Unit, integration, guardrails & evaluation tests
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
└── pytest.ini
```

---

## 3. Installation & Setup

### Prerequisites
- Python 3.10 to 3.14
- Git

### Windows PowerShell
```powershell
# 1. Clone repository and navigate to folder
cd "AI NEWS AND RESEARCH AGENT"

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup configuration
Copy-Item .env.example .env
```

### macOS / Linux
```bash
# 1. Clone repository and navigate to folder
cd "AI NEWS AND RESEARCH AGENT"

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup configuration
cp .env.example .env
```

---

## 4. Local Ollama & Qwen Model Setup (Optional)
The application operates fully in **Heuristic Fallback Mode** without Ollama. To enable local AI analysis with Qwen:

1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai).
2. **Start Ollama Service**:
   ```bash
   ollama serve
   ```
3. **Pull Qwen Model**:
   ```bash
   ollama pull qwen2.5:7b
   ```
4. Verify local availability:
   ```bash
   curl http://localhost:11434/api/tags
   ```

---

## 5. Running the Application

### Launch Streamlit Dashboard
```bash
streamlit run frontend/streamlit_app.py
```
Open your browser at `http://localhost:8501`.

### Run via Command-Line Interface (CLI)
```bash
# Fetch and analyze AI News & arXiv papers
python app/main.py --domain ai_news --refresh

# Fetch and analyze Cricket News
python app/main.py --domain cricket --refresh

# Fetch and analyze Geopolitics
python app/main.py --domain geopolitics --refresh
```

### Run Daily Briefing Pre-fetcher
```bash
python scheduler/daily_briefing.py
```

---

## 6. Running Tests & Quality Verification

Run the complete test suite:
```bash
pytest
```

Run test suite with detailed coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

Run specific test categories:
```bash
# Unit tests
pytest tests/unit -v

# Guardrail & security tests (SSRF, prompt injection)
pytest tests/guardrails -v

# LangGraph integration tests
pytest tests/integration -v

# Ranking evaluation benchmarks
pytest tests/evaluation -v
```

---

## 7. Troubleshooting & Operational FAQs
- **Feed Returns 404 or Timeout**: External feeds are monitored by `SourceHealth`. If an external endpoint is unreachable, the error is isolated, logged as degraded, and other sources continue processing normally.
- **Ollama Offline**: If Ollama is not running, the application displays a yellow telemetry status: `🟡 Heuristic Fallback (Offline Mode)` and directly provides extracted source paragraphs without hallucination.
- **SSRF Blocked**: User queries or custom source URLs targeting private ranges (`127.0.0.1`, `10.0.0.0/8`, `169.254.169.254`) are intercepted and rejected with an `SSRFProtectionError`.
