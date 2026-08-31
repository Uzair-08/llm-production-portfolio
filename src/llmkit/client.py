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

from openai import APIStatusError, OpenAI, RateLimitError

from .config import get_settings
from .logging_setup import log_event

log = logging.getLogger("llmkit.client")

PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "gemini-3.5-flash": (1.50, 9.00),
    "llama-3.3-70b-versatile": (0.59, 0.79),
}

# Map each model name to the base_url it needs. This is what lets one
# client class talk to multiple OpenAI-compatible providers.
PROVIDER_BASE_URLS: dict[str, str] = {
    "gemini-3.5-flash": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "llama-3.3-70b-versatile": "https://api.groq.com/openai/v1",
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    inp, outp = PRICES_PER_MTOK.get(model, (0.0, 0.0))
    return (input_tokens * inp + output_tokens * outp) / 1_000_000


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    raw: object = field(default=None, repr=False)


class LLMClient:
    def __init__(self, model: str | None = None, fallback_model: str | None = None):
        self.settings = get_settings()
        self.model = model or self.settings.default_model
        self.fallback_model = fallback_model or self.settings.fallback_model

    def _client_for(self, model: str) -> OpenAI:
        """Build the right OpenAI-compatible client for a given model name."""
        if model.startswith("gemini"):
            api_key = self.settings.gemini_api_key
        elif model.startswith("llama"):
            api_key = self.settings.groq_api_key
        else:
            raise ValueError(f"Don't know which API key to use for model: {model}")
        return OpenAI(
            api_key=api_key,
            base_url=PROVIDER_BASE_URLS[model],
            timeout=self.settings.request_timeout_s,
        )

    def _call_once(self, model: str, prompt: str, system: str | None,
                    max_tokens: int, temperature: float):
        """One attempt at one model. No retry logic here — that's the caller's job."""
        client = self._client_for(model)
        messages = []
        # TODO 1: if `system` is provided, add {"role": "system", "content": system}
        #         to `messages` first.
        if system:
            messages.append({"role": "system", "content": system})
    
    
        # TODO 2: append {"role": "user", "content": prompt} to `messages`.

        messages.append({"role": "user", "content": prompt})
        # TODO 3: call client.chat.completions.create(model=model, messages=messages,
        #         max_tokens=max_tokens, temperature=temperature) and return the result.
        return client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature)
        

    def complete(self, prompt: str, system: str | None = None,
                 max_tokens: int = 1024, temperature: float = 0.0) -> LLMResponse:
        start = time.perf_counter()
        model_used = self.model
        resp = None
        try:
            resp = self._call_once(model_used, prompt, system, max_tokens, temperature)
        except (RateLimitError, APIStatusError) as e:
            log.warning(f"Model {model_used} failed with {type(e).__name__}, "
                        f"retrying with fallback model {self.fallback_model}...")
            model_used = self.fallback_model
            resp = self._call_once(model_used, prompt, system, max_tokens, temperature) 
            
        # TODO 4: try self._call_once(self.model, ...) inside a try/except.
        #         Catch (RateLimitError, APIStatusError) specifically — NOT
        #         bare Exception (this is the fix you identified yourself
        #         on Day 5). On that specific failure, log a warning and
        #         retry with self.fallback_model instead, updating model_used.
        #         Let any OTHER exception type propagate uncaught (a real bug
        #         should crash loudly, not be silently swallowed).

        latency_ms = (time.perf_counter() - start) * 1000
        text = resp.choices[0].message.content.strip()
        in_tok = resp.usage.prompt_tokens
        out_tok = resp.usage.completion_tokens
        cost = estimate_cost(model_used, in_tok, out_tok)

        log_event(
            log, "llm_call",
            model=model_used, cost_usd=round(cost, 6),
            latency_ms=round(latency_ms), in_tok=in_tok, out_tok=out_tok,
        )

        return LLMResponse(
            text=text, model=model_used, input_tokens=in_tok,
            output_tokens=out_tok, latency_ms=latency_ms,
            cost_usd=cost, raw=resp,
        )
    
    def complete_structured(self, prompt: str, schema: type, **kw):
        """WEEK 2 Day 2: JSON/tool-calling extraction validated by a pydantic
        model, with one repair-and-retry on validation failure."""
        raise NotImplementedError("Week 2, Day 2: implement me.")
