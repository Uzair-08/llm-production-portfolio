# Decision log

One entry per meaningful choice. Senior engineers are distinguished by being
able to say WHY, months later. Format: date — decision — why — alternatives rejected.

## 2026-07-10 — Repo structure
- Single portfolio monorepo; shared `llmkit` package; each week's project imports it.
- Why: reuse proves the abstractions are right; becomes the interview portfolio.
- Rejected: repo-per-project (duplicated wrappers, no compounding).

## 2026-07-10 — Using free API tiers for the 16-week course
- Decision: Google AI Studio (Gemini) as primary provider, Groq as a future fallback.
- Why: zero cost, no credit card, 1,500 req/day is well above my learning volume.
  Also forces multi-provider design from day one — a real production skill.
- Caveat: free tier means Google may use my prompts to improve their models.
  Rule: public / synthetic data only in this repo. Never paste anything from
  my internship or anything personal into a call.
- Rejected (for now): paid Anthropic Console access. Will revisit if a specific
  project needs Claude-specific features.

## 2026-07-10 — Why every LLM call goes through llmkit.LLMClient
- All projects import from `llmkit` instead of calling provider SDKs directly.
- Reason 1 — swap without rewrite: switching Gemini → Claude → Groq is a config
  change, not a code change in every project. The provider lives in one file.
- Reason 2 — instrumentation once, benefit everywhere: retries, cost accounting,
  logging, timeouts live in the wrapper. Every project I build gets these for
  free just by using the wrapper.
- Reason 3 — future migrations: providers deprecate models (I hit this today
  on Day 1). If every project called Gemini directly, a deprecation would mean
  editing every project. With the wrapper, it's one edit.
- Rejected: calling the OpenAI/Anthropic SDK directly in each project. Faster
  to start, catastrophic to maintain.

## 2026-07-10 — Chose gemini-3.5-flash (pinned) over gemini-flash-latest (alias)
- Pinned wins on reproducibility: my outputs and costs won't change unless I
  change them.
- Alias wins on convenience but hides silent model swaps — Google can change
  what "-latest" points to without telling me, and my behavior/costs shift.
- Fallback identified: gemini-2.5-flash (confirmed available via ListModels).
- Rule: always call the discovery endpoint before trusting a model name from
  docs, tutorials, or an AI assistant. Model availability varies by account.

## 2026-07-10 — Hit Gemini model deprecation on Day 1
- Symptom: 404 "no longer available to new users" on gemini-2.5-flash, then
  the same on gemini-3-flash. Docs said one thing; my account said another.
- Cause: Google migrated the free-tier default between my knowledge sources
  and the actual state of my account.
- Fix: called ListModels endpoint → picked gemini-3.5-flash from the real list
  → updated .env, price table, test, and script. One coherent change.
- Lesson: providers move faster than docs. Discovery endpoints are the source
  of truth. Design so a model swap is a config change, not code editing.

## 2026-07-10 — First-call observations from hello_gemini.py
- First-call latency: ~15.8 seconds. Massive by production standards.
  Likely cold start + hidden reasoning tokens.
- Gotcha found: max_tokens=150 truncated output to 5 tokens because Gemini 3.x
  spends part of the budget on internal thinking. Bumped to 1024.
- Cost per short reply: ~$0.00002. Cumulative cost matters more than per-call.
- Silenced httpx INFO log noise; kept my own structured JSON log line.
- Rule for Week 2: measure p50 AND p95 separately. Averages hide first-call pain.

## 2026-07-10 — Silent config failure is a known limitation
- Current: when .env is missing, gemini_api_key defaults to "" and tests pass.
  First real API call then fails with a cryptic upstream auth error.
- Better for production: fail loud at startup — "no key configured for the
  default model." Users find out immediately, not three layers deep in a trace.
- Deferred deliberately: I'll add fail-loud validation in Week 2 when I
  implement client.py, since that's where "which key does this model need?"
  logic will naturally live. Not everything gets fixed the moment it's found.

## 2026-07-10 — Test caught a real bug during the model rename
- Renamed gemini-2.5-flash → gemini-3.5-flash in PRICES_PER_MTOK but forgot
  test_cost.py. pytest failed loudly: `0.0 == 2.8`.
- Without this test, cost accounting would have silently reported $0 for every
  Gemini call. Billing dashboard and reality would diverge until the invoice.
- Lesson: model IDs are cross-file identifiers. Grep before renaming, or
  extract to a named constant so there's one source of truth. Considering
  a `DEFAULT_MODEL_ID` constant for Week 2.

## 2026-07-10 — Adopted ruff and ruff --fix
- Ruff caught unused imports (F401) and unsorted imports (I001) in code I
  wrote today. --fix auto-organized imports per PEP 8.
- Workflow going forward: `ruff check . --fix` before every commit; review the
  diff, then commit. Trust the tool, verify the result.
- Later (Month 3): wire ruff into a pre-commit hook so bad formatting can't
  even reach a commit.

## 2026-07-10 — Understood estimate_cost and its role in observability
- The function does dictionary lookup with a safe fallback of (0.0, 0.0) and
  computes (input_tokens × price_in + output_tokens × price_out) / 1_000_000.
- Confirmed by hand-calculating my first real Gemini call: 18 in, 5 out,
  at (0.30, 2.50) prices = $0.0000179 → matched the logged 1.8e-05.
- Why it matters: every call throughout the 16 weeks produces a comparable
  cost number in the same log format. When someone asks "what does this
  feature cost per user per day?" — that answer exists in the logs, not a bill.