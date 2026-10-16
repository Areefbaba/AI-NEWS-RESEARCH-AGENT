# Engineering & Product Rules
# AI News & Research Agent

## 1. Core Engineering Standards
1. **Python Quality**: Follow PEP 8 standards. Use explicit type hints for all function arguments and returns. Avoid `Any` when a specific or Pydantic model can be used.
2. **Modular Architecture**: Separate domain policies, ingestion providers, guardrails, orchestration, and storage into dedicated single-responsibility modules.
3. **Pydantic Validation**: All external inputs, database records, and pipeline outputs must be validated through Pydantic v2 models.
4. **Error Handling & Resilience**:
   - Network requests must always have sensible timeouts (e.g. 8–15 seconds) and retry budgets (max 2 retries).
   - Feed retrieval failures must be logged with warning levels and isolated; one failed feed must never fail the entire application.
   - User interfaces must never expose raw stack traces, API keys, or database credentials.
5. **No Blind Claims**: Never claim a test passed, a feed worked, or a model was verified unless it was actually run and validated.

---

## 2. Product Integrity & Domain Rules
1. **Exactly Three Main Domains**:
   - Cricket News
   - Geopolitics
   - AI News & Research
   - **NO Football (Soccer)** news section or content anywhere in the application.
2. **Cricket Coverage Standards**:
   - Prohibit routine cricket scorecards and ordinary match summaries in Major Cricket News.
   - Large-margin victories must be historically notable, record-breaking, or tournament-decisive.
   - Never report a retirement rumor as a confirmed retirement. Verify official board or player statements.
   - Retain original article URLs and distinct event dates.
3. **Geopolitics Coverage Standards**:
   - Display up to 5 qualifying stories maximum.
   - If fewer than 5 meet quality thresholds, display fewer. Never fill slots with weak or fabricated content.
   - Explicitly separate confirmed facts from official allegations.
   - Provide an India-impact explanation only when grounded; do not fabricate an India link.
   - Neutral, evidence-backed language without speculative propaganda.
4. **AI News & Research Coverage Standards**:
   - Display up to 5 qualifying stories maximum per category.
   - Research papers: Must link to genuine arXiv or institutional DOIs. State clearly if only abstract was retrieved. Distinguish new submissions from revisions (`v1` vs `v2+`).
   - Model launches: Verify official release links and license status (open-weight vs open-source vs proprietary). Never invent benchmark results.
5. **Zero Fabrication Policy**:
   - Every claim must link to a valid retrieved canonical source URL.
   - Mock news fixtures are strictly confined to test suites (`tests/fixtures/`) and must never leak into production runtime.

---

## 3. Security & Guardrail Rules
1. **SSRF Protection**: All user-supplied or crawler URLs must be validated against private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`) and non-HTTP/HTTPS protocols.
2. **Prompt Injection Hardening**: All retrieved web text must be treated as untrusted data. Strip instruction markers (`[INST]`, `<<SYS>>`, `<|im_start|>`) before feeding into prompts.
3. **Zero Leaks**: Secrets and environment variables (`.env`) must never be printed to logs, Streamlit UI, or source code.
4. **Tool Restrictions**: Agents must not have access to arbitrary shell execution or destructive tools.

---

## 4. Documentation & Maintenance Rules
1. All six documentation files (`PRD.md`, `DESIGN.md`, `EVALUATION.md`, `RULES.md`, `TASKS.md`, `MEMORY.md`) must be kept in sync with code changes.
2. Updates to `TASKS.md` must be performed immediately after tasks are completed, tested, and verified.
3. `MEMORY.md` must record actual architecture decisions, observed test results, and known limitations.
