"""Day 1 smoke test: does our Gemini key actually reach Gemini?

Not a unit test (needs network + real API). Run it manually with:
    python scripts/hello_gemini.py
"""

import logging
import time

from openai import OpenAI

from llmkit import estimate_cost, get_settings, log_event, setup_logging

setup_logging()
log = logging.getLogger("hello_gemini")
settings = get_settings()

# Gemini exposes an OpenAI-compatible endpoint. This is the pattern you'll
# formalize inside LLMClient in Week 2 — for now, we do it inline to see it work.
client = OpenAI(
    api_key=settings.gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

prompt = "how many r's are in the word 'strawberry'?"

start = time.perf_counter()
resp = client.chat.completions.create(
    model="gemini-3.5-flash",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=1024,
)
latency_ms = (time.perf_counter() - start) * 1000

in_tok = resp.usage.prompt_tokens
out_tok = resp.usage.completion_tokens
cost = estimate_cost("gemini-3.5-flash", in_tok, out_tok)

print("\n--- Gemini says ---")
print(resp.choices[0].message.content)
print("-------------------")
log_event(
    log,
    "llm_call",
    model="gemini-3.5-flash",
    in_tok=in_tok,
    out_tok=out_tok,
    cost_usd=round(cost, 6),
    latency_ms=round(latency_ms),
)
