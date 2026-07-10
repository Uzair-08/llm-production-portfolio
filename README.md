# llm-production-portfolio

My 16-week production AI engineering portfolio. Everything here compounds:
each project reuses `llmkit` (client, config, logging), which grows every week.

## Day 1 checklist (do these in order, ~2 hours)

- [ ] **(15 min)** Install `uv` (https://docs.astral.sh/uv/), then in this repo:
  `uv venv && source .venv/bin/activate && uv pip install -e ".[dev]"`
- [ ] **(5 min)** `cp .env.example .env`, add your Anthropic API key.
- [ ] **(10 min)** Run `pytest -q` → 3 tests pass. Run `ruff check .` → clean.
- [ ] **(30 min)** Read every file in `src/llmkit/` INCLUDING the docstrings —
  they explain the production reasoning. Rusty on anything (decorators,
  dataclasses, lru_cache, type hints)? Look it up NOW with the concrete code
  in front of you. This is your Python refresher, anchored to real use.
- [ ] **(30 min)** Break things on purpose (senior habit: know your failure modes):
  - Delete `.env` → run a script importing `get_settings()` → observe behavior.
  - Change a price in `PRICES_PER_MTOK` → watch the test fail → revert.
  - Add a deliberate lint error → `ruff check .` → fix it.
- [ ] **(20 min)** `git init`, first commit, push to GitHub (private is fine).
- [ ] **(10 min)** Add one entry to `docs/DECISIONS.md` in your own words:
  why does every LLM call go through a wrapper instead of calling the SDK
  directly? If you can't write 3 sentences, reread `client.py`'s docstring.

**Day 1 done =** tests green, repo on GitHub, decision log entry written.

## Repo map

```
src/llmkit/          the toolkit that grows all 16 weeks
  config.py          settings & secrets (pydantic-settings)
  logging_setup.py   structured JSON logging
  client.py          LLM wrapper — SKELETON now, implemented in Week 2
tests/               pytest; grows with every module
evals/               golden sets + eval configs (starts Week 4)
docs/DECISIONS.md    the "why" log — interview gold
```

## What gets added when

- **Week 2:** implement `client.py` (retries, cost, structured outputs, streaming)
- **Week 3:** `retrieval/` (chunking, hybrid search, retrieval metrics)
- **Week 4:** `projects/p1_doc_qa/` + first golden set in `evals/`
- **Week 6:** promptfoo/eval harness wired to `evals/`
- **Week 9+:** routing & caching in the client; **Week 11:** tracing; **Week 12:** gateway service
