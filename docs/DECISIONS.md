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

  ## 2026-07-14 — Day 2: what tokens actually are
- Tokens are the "atoms" LLMs operate on — smallest unit, not letters and not words.
- BPE (byte-pair encoding) merges frequent UTF-8 byte-pairs into single tokens, so
  common patterns get compressed into big tokens over training.
- Why not characters? Attention is O(n²) in sequence length — character-level
  would explode compute and shrink context windows. Why not words? Can't handle
  new/misspelled/compound words. BPE is the middle ground.
- Strawberry can't be counted because it's ~2 tokens; the model can't "see" the
  individual r's inside those opaque chunks — it can only predict from patterns.
- Spacing letters ("s t r a w b e r r y") forces one-token-per-letter, so
  attention can now count them across positions. Same reason chain-of-thought
  prompting works: more visible tokens = more attention workspace.

## 2026-07-14 — Multilingual tokenization cost
- Higher chars/token = more efficient. In my experiment: English ~4.3,
  Hindi ~3.4, Telugu ~1.9 → Telugu is the most expensive per unit of text.
- Cause: BPE prioritizes byte-pairs that appeared frequently in training.
  English dominated training, so English got large merged tokens. Indian
  scripts stayed as tiny 1–2 byte tokens because their pairs were too rare.
- Business implication (matters to me personally as an Indian FDE): serving
  Hindi/Telugu users can cost 2–4x more per interaction than English. In
  consumer apps the user doesn't see this, but the company pays it. In an
  FDE engagement with an Indian customer, this is a real line item that
  affects model choice and unit economics.

## 2026-07-14 — Emoji "chars/token < 1" revealed a measurement bug
- Observed: some emoji strings had chars/token ratio below 1. Initially
  thought this meant character-level tokenization is more efficient.
- Actually: Python's len() counts code points, not visual characters or bytes.
  Compound emoji (family, skin tone) are multi-code-point sequences joined
  by invisible ZWJ characters. And each simple emoji is already 3–4 UTF-8
  bytes. So one emoji becomes multiple tokens while len() counts it as 1.
- Correct efficiency measure is bytes/token, not chars/token, because BPE
  operates on UTF-8 bytes.
- Character-level tokenization is NOT better anywhere. Reasons: (1) O(n²)
  attention explodes when sequences get ~4x longer; (2) context windows
  shrink proportionally (128k tokens → ~25k characters, useless for real docs).

## 2026-07-14 — Prompt caching depends on exact-token prefix matches
- Providers cache the compute for token prefixes. If a new request's prefix
  is byte-identical to a recent one, they skip recomputing and charge ~10%
  of normal price — a ~90% discount on the cached portion.
- "hello" vs " hello" vs "Hello" are three different tokens. One extra space
  in a system prompt = totally different cache key = full price.
- Design rule for building prompts: static content (system prompt, tool defs,
  KB context) goes at the top; variable user input goes at the bottom.
  If variables come first, every request has a different prefix and caching
  never fires. That's a real production cost bug hiding in prompt structure.

## 2026-07-14 — Gemini 503 incident during Day 2
- Symptom: 3 consecutive 503 UNAVAILABLE errors on gemini-3.5-flash. OpenAI
  SDK auto-retried with exponential backoff (0.43s, 0.77s, ~1.5s) before
  giving up. Message from Gemini: "high demand, try again later."
- Cause: free-tier capacity contention, not my code. This is roadmap
  failure mode #5 (rate-limit blowups) in the wild.
- Retries alone don't solve capacity problems — they only help with truly
  fleeting failures. If the provider is genuinely under load, retrying just
  delays the crash and burns latency budget.
- Two separate things to add in Week 2 client.py:
  * Technical: model/provider fallback — on primary failure after retries,
    try a fallback model (gemini-2.5-flash) before surfacing the error.
  * Product: if all fallbacks fail, return a clean user-facing message,
    not a stack trace. Degrade gracefully.

## 2026-07-14 — Ruff E501 (line too long) on a comment
- Ruff flagged a 121-char comment against my project's 100-char limit.
- Three options I had: (1) wrap the comment across multiple lines,
  (2) `# noqa: E501` to suppress just that line, (3) raise line-length
  in pyproject.toml project-wide.
- Chose (1). Reason: it's the local fix with no debt and no project-wide
  policy shift for a single comment. `noqa` is debt (every one normalizes
  ignoring warnings); raising the project limit is a big decision made
  reactively for a small problem.
- Rule going forward: fix warnings by default; suppress only when there's
  a real reason (unbreakable URL, long string literal); change project
  rules deliberately, once, not reactively.