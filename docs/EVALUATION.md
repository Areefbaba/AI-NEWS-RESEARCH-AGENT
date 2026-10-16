# Evaluation Strategy & Quality Framework
# AI News & Research Agent

## 1. Overview & Evaluation Principles
This document outlines the testing, verification, and evaluation strategies for the AI News & Research Agent.
To adhere to product standards:
- **No Fabricated Evaluation**: We never claim evaluation metrics that have not been observed.
- **Deterministic Fixtures**: Automated unit tests use synthetic, reproducible fixture data instead of relying on live internet connections or stochastic LLM outputs.
- **Live Integration Tests**: Kept in a dedicated test suite with proper mocking/skip flags when offline.
- **Strict Guardrail Testing**: Verification of SSRF defenses, prompt injection mitigations, and citation integrity.

---

## 2. Evaluation Metrics & Thresholds

| Metric | Target Threshold | Description |
|---|---|---|
| **Citation Validity Rate** | 100% | Every displayed claim must trace directly to a verified retrieved canonical URL. |
| **Routine Cricket Rejection Rate** | $\ge 95\%$ | Routine ball-by-ball scorecards and ordinary match reports must be excluded from Major Cricket News. |
| **Top-5 Geopolitics Relevance** | $\ge 90\%$ | Geopolitics stories must cover major international security, treaties, elections, or India-strategic developments. |
| **AI Paper Metadata Completeness** | 100% | Title, authors, submission date, arXiv ID, abstract, and link must be preserved without hallucination. |
| **Deduplication Precision** | $\ge 95\%$ | Parallel reports of the identical event must be clustered together without dropping distinct news events. |
| **Graceful Degradation** | 100% | In the absence of Ollama/Qwen, the pipeline must complete using heuristic summaries without errors. |
| **SSRF / Tool Safety** | 100% | Block 100% of internal IP requests (`127.0.0.1`, `10.0.0.0/8`, `169.254.169.254`). |

---

## 3. Test Suites & Organization

```
tests/
├── unit/
│   ├── test_schemas.py           # Pydantic data model validation
│   ├── test_normalization.py     # HTML cleaning, date parsing, fingerprinting
│   ├── test_deduplication.py     # Story clustering & canonical selection
│   ├── test_ranking.py           # Multi-factor score computation
│   ├── test_cricket_policy.py    # Cricket exclusion of routine scorecards
│   ├── test_geopolitics_policy.py# Geopolitical ranking and India impact
│   ├── test_ai_policy.py         # arXiv metadata parsing & model releases
│   └── test_llm_service.py       # Ollama integration & heuristic fallback
├── integration/
│   ├── test_rss_reader.py        # RSS ingestion with mock and live feeds
│   ├── test_arxiv_client.py      # arXiv API extraction with mock responses
│   ├── test_sqlite_storage.py    # Database migrations, caching TTL, queries
│   └── test_workflow_graph.py    # LangGraph end-to-end execution
├── guardrails/
│   ├── test_input_guardrails.py  # Query validation and length bounds
│   ├── test_prompt_injection.py  # Injection resistance in article text
│   ├── test_tool_guardrails.py   # SSRF rejection of private IPs & bad schemes
│   └── test_output_guardrails.py # Citation linkage & ungrounded claim checks
└── evaluation/
    ├── test_ranking_eval.py      # Evaluation against benchmark story sets
    └── eval_dataset.json         # Labeled test dataset for domain ranking
```

---

## 4. Benchmark Evaluation Dataset Schema (`eval_dataset.json`)
```json
{
  "test_cases": [
    {
      "id": "cricket_001",
      "domain": "cricket",
      "category": "major_news",
      "title": "India crush Australia by an innings and 222 runs in record Test victory",
      "is_routine_scorecard": false,
      "expected_eligible": true,
      "expected_min_score": 0.70
    },
    {
      "id": "cricket_002",
      "domain": "cricket",
      "category": "major_news",
      "title": "Ranji Trophy Day 2: Baroda 145/4 vs Odisha 120",
      "is_routine_scorecard": true,
      "expected_eligible": false,
      "expected_min_score": 0.0
    },
    {
      "id": "geopolitics_001",
      "domain": "geopolitics",
      "title": "India and France sign landmark defense co-production pact on jet engines",
      "expected_india_relevance": true,
      "expected_min_score": 0.75
    },
    {
      "id": "ai_001",
      "domain": "ai_news",
      "category": "research_papers",
      "title": "Qwen 2.5-Coder: Technical Report on Open Code Models",
      "has_valid_arxiv": true,
      "expected_min_score": 0.80
    }
  ]
}
```

---

## 5. Execution Instructions
To execute the automated test suites:
```powershell
# Run all unit tests
pytest tests/unit -v

# Run guardrails security tests
pytest tests/guardrails -v

# Run end-to-end integration tests
pytest tests/integration -v

# Run complete test suite with coverage
pytest --cov=app --cov-report=term-missing tests/
```
