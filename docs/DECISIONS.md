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

  ## 2026-07-15 — Day 3: how a transformer actually generates text

### 1. One token at a time — the mechanism
Generation is a loop of forward passes. Each pass produces logits over the whole
vocabulary; softmax turns them into probabilities; we sample one token, append it
to the input, and repeat. The model has no plan — no held-in-mind paragraph
structure — just "given these tokens, what's the next one most likely to be."

Production implications:
- Streaming responses are natural — tokens can be sent to the user as they're
  generated, since each is produced independently.
- Output tokens cost 3-5x more than input tokens because each requires its
  own forward pass; input tokens are processed once, in parallel.
- The model can never revise an earlier token. Once emitted, it's context.

### 2. Temperature reshapes the probability distribution
Before applying softmax, logits are divided by T: `softmax(logits / T)`.
- T < 1 → sharper distribution (top token dominates more).
- T = 1 → raw distribution.
- T > 1 → flatter distribution (lower-probability tokens get more chance).

Confirmed in my experiment: at T=0.1 the top token was >50% probability;
at T=2.0 the top 4 tokens were all around 10-20% — the model becomes
essentially random.

### 3. Why T=0 is NOT perfectly deterministic in production
This one I got wrong on first try and had to learn. In theory T=0 = greedy =
always pick argmax = deterministic. In practice, the same prompt at T=0 can
produce different outputs across runs.

Cause: floating-point non-determinism in batched GPU inference. Providers batch
multiple users' requests together to maximize GPU throughput. Batch composition
changes the order of matrix multiplications at the hardware level.
Floating-point math isn't perfectly associative — (a+b)+c can differ from
a+(b+c) in the last few bits. Occasionally those tiny differences flip which
token has the highest logit.

Production implication: LLM evals cannot use exact string matching, even at
T=0. Use semantic checks (contains X? LLM-judge score above threshold?)
instead of `assert output == "expected"`.

### 4. Top-k and top-p filter the tail; different job than temperature
Temperature and top-p solve different problems:
- Temperature reshapes the whole distribution (sharper vs. flatter).
- Top-k/top-p CUT OFF the long tail of low-probability tokens before sampling.

Even at moderate temperature, the distribution has thousands of tokens with
tiny probabilities. Sampling from the full distribution occasionally rolls
weird tokens and produces garbage. Top-p (keep enough top tokens to cover
90% of probability mass) prunes the tail so sampling stays in the plausible
zone.

Analogy: temperature = how hard you shake the dice. Top-p = removing the
loaded faces before you roll.

Production defaults I'll use in Week 2:
- Extraction / classification / factual: T=0.
- General chat / summarization: T=0.7, top_p=0.9.
- Creative writing: T=1.0, top_p=0.95.

### 5. Watched hallucination happen mechanically
Ran greedy decoding on "The three laws of robotics are" — model output:
"The robot must be able to do the job." Fluent English, grammatically correct,
factually wrong. Asimov's actual three laws don't appear. Not a bug — the
model chose the highest-probability continuation at each step, and that
completion IS statistically plausible in English text. Fluency ≠ accuracy.
This is the mechanism behind hallucination and why RAG (grounding on
retrieved documents) matters.

### 6. Smaller models miss facts larger models get
Ran the same prompts on gpt2 (124M) vs gpt2-medium (355M). "2+2=" gave
"3" on gpt2 and "4" on gpt2-medium. Same architecture, more parameters
and training → real capability difference. This is the "capabilities emerge
with scale" phenomenon at small scale, live in my terminal — the same
reason frontier models keep improving as they scale up.

## 2026-07-XX — Day 4: embeddings and semantic search

### 1. What an embedding is
An embedding is a vector representation of text — not necessarily a single
word, could be a phrase, sentence, or chunk (1+ tokens). It's produced by
passing the text through multiple transformer layers, which combine and
refine the token representations into one vector that captures the overall
meaning of the passage.

### 2. Embeddings capture structure/topic more than sentiment
"I love pizza" and "I hate broccoli" scored 0.42 — higher than "I love pizza"
vs "I love programming" (0.45, barely higher). Both pizza/broccoli sentences
share the same shape: person + emotional verb + food noun. The model picked
up on that shared structure even though "love" and "hate" are opposite
sentiments. Lesson: embeddings capture topic/structure more strongly than
polarity — semantic similarity is not the same as semantic agreement.

### 3. Semantic search finds paraphrases without needing shared vocabulary
Query "how do I get a refund" ranked the correct doc first even though the
word "refund" wasn't in it — the model matched on meaning ("return policy"
≈ "refund"). Production win: users never phrase questions exactly like the
documentation. If retrieval required literal keyword overlap, every possible
user phrasing would need to be anticipated. Semantic search lets docs and
queries be written naturally and still connect.

### 4. Where semantic search fails — exact matches / negation — and the fix
Query "error code E-4012": a short, unrelated joke doc containing the literal
phrase "error code" nearly outranked the genuinely useful troubleshooting doc,
because the joke doc's vector was dominated by those matching words.
Fix: hybrid search — combine embedding similarity (semantic) with BM25/keyword
scoring (lexical), then merge the rankings. This covers both paraphrase
matching and exact-identifier matching.

Related finding: cosine similarity is more reliable on longer, information-rich
text. Short chunks get dominated by whichever words are present (surface
overlap), while longer chunks let real meaning average out more accurately.
Confirmed by padding the banana joke with more text — its score against the
query DROPPED once it stopped being just about "error code" and became a
grab-bag about bananas generally.

### 5. When to use embeddings vs. not
Use embeddings: semantic search over natural-language documents, e.g. finding
KB articles for phrased-differently user questions (Experiment 2).
Don't rely on embeddings alone: exact-identifier lookups (order numbers,
error codes, SKUs), negation-sensitive queries, or sentiment-polarity
distinctions — all shown to fail or blur in today's experiments.

### 6. The same-model gotcha
Corpus and query embeddings MUST come from the same model. Different models
produce vectors in incompatible spaces — not just different dimension counts,
but genuinely different representations of the same sentence (proven directly:
MiniLM and mpnet gave very different similarity scores for identical sentence
pairs today). If the embedding model is ever upgraded, the entire corpus must
be re-embedded before queries will work correctly — a real migration cost to
plan for, not a drop-in swap.

### Bonus finding — model size affects topic resolution
Same 5 sentences ("I love burgers/pizza/biryani/school/embeddings"), two models:
- MiniLM (384-dim): burgers↔biryani = 0.19, burgers↔school = 0.23 — WRONG,
  ranked an unrelated topic (school) closer than a same-topic pair (food).
- mpnet (768-dim): burgers↔biryani = 0.30, burgers↔school = 0.17 — CORRECT,
  topic now dominates over surface sentence structure.
Cause: more dimensions give the model more room to keep different signals
(topic vs. sentence style) from overlapping/interfering. Bigger, better-trained
models resolve fine distinctions that small models blur — but dimension count
alone isn't the cause, it's a proxy for model capacity and training quality.
Production tradeoff: bigger embedding models cost ~2x compute/storage at
scale. Worth it when retrieval quality on closely-related short text matters;
often unnecessary for long, information-rich documents (Experiment 2 worked
fine on MiniLM).

### Also: bare identifiers embed poorly; context helps
Tested query "E-4012" alone vs. "error code E-4012" vs. "problem with router
E-4012 restart" against the same doc set. The bare identifier scored WORST
(0.394) for the correct doc — worse than the version with full sentence
context (0.709). Short, low-context queries produce noisy vectors; embeddings
need semantic context to work well. This is additional evidence for why
bare identifiers should route through keyword/BM25 search rather than
semantic