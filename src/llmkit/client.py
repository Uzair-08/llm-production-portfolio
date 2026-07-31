"""LLM client wrapper — the single most-reused file of your 16 weeks.

DAY 1: this is a typed SKELETON. You fill in the TODOs during Week 2.
Every project (RAG, chatbot, extraction, agents) will call THIS instead of
calling providers directly, because this is where production behavior lives:
retries, timeouts, cost accounting, logging.

Design notes (read these — they're the lesson):
- One internal interface, many providers behind it -> switching models later
  is a config change, not a rewrite (the 'gateway' pattern in miniature).
- Every call returns LLMResponse with tokens/cost/latency attached. If you
  can't answer 'what did that request cost?', you're not production-ready.
- Retries use exponential backoff + jitter, and ONLY on retryable errors
  (429, 5xx, timeouts). Never retry a 400 — it will fail identically forever.
"""

import logging
import time
from dataclasses import dataclass, field

from .config import get_settings
from .logging_setup import log_event  # noqa: F401  (used in Week 2 impl)

log = logging.getLogger("llmkit.client")

# Prices per 1M tokens (input, output). Update from provider pricing pages.
# Keeping this table current is a real production chore — automate it later.
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "gemini-3.5-flash": (0.30, 2.50),
    "llama-3.3-70b-versatile": (0.59, 0.79),  # Groq pricing per 1M tokens
    # add models as you use them
}


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    raw: object = field(default=None, repr=False)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    inp, outp = PRICES_PER_MTOK.get(model, (0.0, 0.0))
    return (input_tokens * inp + output_tokens * outp) / 1_000_000


class LLMClient:
    """Provider-agnostic client. Week 2 Day 1-2 work lives here."""

    def __init__(self, model: str | None = None):
        self.settings = get_settings()
        self.model = model or self.settings.default_model

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Single completion with retries, timing, cost, and logging.

        WEEK 2 TODOs (in order):
        1. Call the Anthropic SDK (messages.create) with timeout from settings.
        2. Wrap with tenacity: retry on RateLimitError / APIStatusError 5xx /
           timeouts, exponential backoff + jitter, stop after settings.max_retries.
        3. Extract usage tokens from the response; compute cost via estimate_cost.
        4. log_event(...) the call: model, tokens, cost_usd, latency_ms,
           and (if settings.log_prompts) a TRUNCATED prompt — never full PII.
        5. Return LLMResponse.
        """
        start = time.perf_counter()  # noqa: F841  (used in Week 2 impl)
        raise NotImplementedError("Week 2, Day 1: implement me.")
        # skeleton of the shape you'll return:
        # latency_ms = (time.perf_counter() - start) * 1000
        # resp = LLMResponse(text=..., model=self.model, input_tokens=...,
        #                    output_tokens=..., latency_ms=latency_ms,
        #                    cost_usd=estimate_cost(...), raw=api_response)
        # log_event(log, "llm_call", model=resp.model, cost_usd=resp.cost_usd,
        #           latency_ms=round(resp.latency_ms), in_tok=resp.input_tokens,
        #           out_tok=resp.output_tokens)
        # return resp

    def complete_structured(self, prompt: str, schema: type, **kw):
        """WEEK 2 Day 2: JSON/tool-calling extraction validated by a pydantic
        model, with one repair-and-retry on validation failure."""
        raise NotImplementedError("Week 2, Day 2: implement me.")
