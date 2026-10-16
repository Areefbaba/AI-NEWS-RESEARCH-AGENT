# AI News & Research Agent

[![Live Demo](https://img.shields.io/badge/Render-Live_Production_Demo-00C7B7?style=for-the-badge&logo=render&logoColor=white)](https://ai-news-research-agent-8sec.onrender.com/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Areefbaba/AI-NEWS-RESEARCH-AGENT)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-45%20Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/Areefbaba/AI-NEWS-RESEARCH-AGENT)

🌐 **Live Production URL**: [https://ai-news-research-agent-8sec.onrender.com/](https://ai-news-research-agent-8sec.onrender.com/)

An autonomous intelligence research agent and interactive Streamlit application engineered to discover, score, verify, and summarize current developments across exactly three domains:
1. **Cricket News** (Major records & historic margin victories, Test cricket milestones, decisive international match updates, confirmed player announcements).
2. **Geopolitics** (High-impact security dispatches, diplomatic treaties, bilateral sanctions, and India's strategic foreign policy).
3. **AI News & Research** (Primary arXiv pre-prints, frontier & open-weight foundation model launches, key infrastructure shifts).

> **Core Product Rule**: No fabricated news, no football news, no routine cricket scorecards, mandatory original clickable links, zero-hallucination guarantees, and cascading multi-provider LLM fallbacks.

---

## 1. Key Features & Architecture
- **Agentic Workflow Orchestration**: Built on **LangGraph** with a declarative `StateGraph` linking request validation, multi-source ingestion, canonical normalization, token Jaccard deduplication clustering, multi-factor ranking, and citation guardrails.
- **Explainable Multi-Factor Ranking**:
  $$\text{Score} = w_{\text{rel}} \cdot S_{\text{rel}} + w_{\text{impact}} \cdot S_{\text{impact}} + w_{\text{rec}} \cdot S_{\text{rec}} + w_{\text{src}} \cdot S_{\text{src}} + w_{\text{corrob}} \cdot S_{\text{corrob}}$$
- **Cascading Multi-Provider LLM Fallback Engine**:
  - **Groq Cloud** (`llama-3.3-70b-versatile`) — Ultra-fast primary cloud inference.
  - **Google Gemini** (`gemini-1.5-flash`) — Secondary high-speed commercial fallback.
  - **OpenAI** (`gpt-4o-mini`) — Tertiary resilient cloud fallback.
  - **Local Ollama** (`qwen2.5:7b`) — Private, on-premise local LLM without external network dependencies.
  - **Deterministic Heuristic Synthesizer** — Offline, zero-cost rule-based text synthesis that assembles ~200-word structured analytical briefings directly from verified dispatches with zero hallucinations.
- **Production UI**: Streamlit dashboard featuring dark/light theme adaptive translucent cards (`rgba`), high-density structured metadata tables (`st.dataframe`), and direct provenance links.
- **Enterprise Safety & Guardrails**: Server-Side Request Forgery (SSRF) defense (blocking RFC 1918, loopback, and cloud metadata IPs), prompt injection neutralization, secret redaction, and strict domain boundaries.
- **Embedded Persistence**: SQLite repository with Write-Ahead Logging (WAL) mode and TTL caching for feeds and briefings.

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
│   │   ├── llm.py               # Multi-provider LLM manager & heuristic fallback
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
│       ├── database.py          # SQLite connection manager (WAL mode)
│       └── repository.py        # Persistence & cache CRUD repository
│
├── frontend/
│   └── streamlit_app.py         # Production Streamlit dashboard
├── scheduler/
│   └── daily_briefing.py        # Background daily briefing pre-fetcher
├── docs/
│   └── DESIGN.md                # Complete System Architecture & Design Specification
├── tests/                       # 45 automated unit, integration, guardrails & evaluation tests
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
git clone https://github.com/Areefbaba/AI-NEWS-RESEARCH-AGENT.git
cd "AI-NEWS-RESEARCH-AGENT"

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
git clone https://github.com/Areefbaba/AI-NEWS-RESEARCH-AGENT.git
cd "AI-NEWS-RESEARCH-AGENT"

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

## 4. Multi-Model LLM Configuration

The system functions **100% offline at zero token cost** out of the box using deterministic heuristics. To enable neural synthesis, add your API keys to `.env`:

```env
# Priority order: groq -> gemini -> openai -> ollama -> heuristic
LLM_FALLBACK_ORDER=groq,gemini,openai,ollama,heuristic

# 1. Groq Cloud (Free high-speed tier at https://console.groq.com)
GROQ_API_KEY="gsk_your_groq_api_key_here"
GROQ_MODEL=llama-3.3-70b-versatile

# 2. Google Gemini (Free tier at https://aistudio.google.com)
GEMINI_API_KEY="AIzaSy_your_gemini_api_key_here"
GEMINI_MODEL=gemini-1.5-flash

# 3. OpenAI
OPENAI_API_KEY="sk-your_openai_api_key_here"
OPENAI_MODEL=gpt-4o-mini

# 4. Local Ollama (Qwen)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

---

## 5. Running the Application

### Live Cloud Deployment
The application is deployed live in production on Render:
👉 **[https://ai-news-research-agent-8sec.onrender.com/](https://ai-news-research-agent-8sec.onrender.com/)**

### Launch Streamlit Dashboard Locally
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

Run the complete test suite (45 automated tests):
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

## 7. Documentation
- Detailed architectural decisions, data schemas, and pipeline diagrams are maintained in **[docs/DESIGN.md](docs/DESIGN.md)**.
