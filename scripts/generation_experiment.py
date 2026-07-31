"""Day 3: watch a small model generate one token at a time.

Uses a tiny local model (GPT-2, ~500MB) so we can inspect probabilities
directly — the same mechanism the frontier models use, just smaller.

Answers:
  1. What does the model 'see' when choosing the next token?
  2. Why is 'temperature 0' still non-deterministic in practice?
  3. What is top_p / top_k actually filtering?
"""

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

print("Loading GPT-2 (first run downloads ~500MB, subsequent are instant)...")
tokenizer = GPT2Tokenizer.from_pretrained("gpt2-medium")
model = GPT2LMHeadModel.from_pretrained("gpt2-medium")
model.eval()  # inference mode, no gradients


def next_token_probs(prompt: str, top_k: int = 10):
    """Show the top-k candidate next tokens and their probabilities."""
    ids = tokenizer.encode(prompt, return_tensors="pt")
    with torch.no_grad():
        logits = model(ids).logits[0, -1, :]  # logits for the LAST position
    probs = torch.softmax(logits, dim=-1)  # convert to probabilities
    top = torch.topk(probs, top_k)
    print(f"\nPrompt: {prompt!r}")
    print(f"Top {top_k} candidates for next token:")
    for prob, tid in zip(top.values, top.indices, strict=True):
        piece = tokenizer.decode([tid]).replace("\n", "\\n")
        print(f"  {prob.item():6.2%}  {piece!r}")


# Experiment 1: obvious continuations
print("\n=== Experiment 1: what does the model expect? ===")
next_token_probs("The capital of France is")
next_token_probs("The cat sat on the")
# TODO: predict what the top token will be BEFORE you look. Was your guess in top-3?
# i had predicted paris and mat for this but the paris was on the 4th place and mat wasnt even on
# the top 10
# i saw things like floor, bed and couch.

# Experiment 2: ambiguous vs. concentrated
print("\n=== Experiment 2: entropy — is the model sure? ===")
next_token_probs("2 + 2 =")
next_token_probs("The best programming language is")
# TODO: which one has probability concentrated on 1-2 tokens?
# Which one is spread across many? Why does that difference matter?
# i am predicting that it should show 4 at the top and show languages like python or just maybe i
# might be seeing languages like english, hindi.
# yeah so i was right about 4 as answer it had prob of 20% but the languages were actually
#  programming languages.
# i ran both gpt2 and gpt2-medium and found that the 2+2 = 3 in gpt2 where as gpt2-medium worked
# the other prompt had similar results

# Experiment 3: temperature (do this by hand)
print("\n=== Experiment 3: temperature reshapes probabilities ===")


def temp_effect(prompt: str, temperatures=(0.1, 1.0, 2.0)):
    ids = tokenizer.encode(prompt, return_tensors="pt")
    with torch.no_grad():
        logits = model(ids).logits[0, -1, :]
    print(f"\nPrompt: {prompt!r}")
    for T in temperatures:
        probs = torch.softmax(logits / T, dim=-1)
        top = torch.topk(probs, 5)
        pieces = [tokenizer.decode([tid]).replace("\n", "\\n") for tid in top.indices]
        probs_pct = [f"{p.item():.1%}" for p in top.values]
        pairs = list(zip(pieces, probs_pct, strict=True))
        print(f"  T={T}: {pairs}")


temp_effect("Once upon a time there was a")
# TODO: at T=0.1, is the top token more or less dominant? At T=2.0?
# What does high temperature DO to a probability distribution?

# so when the token was near to 0 the top token was more dominant almost always above 50 and when
# temperatrue aws near 2 the first 4 tokens had similar values like 0.2 0.2 0.1 0.1 which was
# really low and the model can actually choose any thing and might give a very vague response when
# temperature is high.

# Experiment 4: generate a full sentence one token at a time
print("\n=== Experiment 4: generation is a loop ===")
prompt = "The three laws of robotics are"
ids = tokenizer.encode(prompt, return_tensors="pt")
for step in range(15):
    with torch.no_grad():
        logits = model(ids).logits[0, -1, :]
    next_id = torch.argmax(logits).unsqueeze(0)  # greedy: pick the max
    ids = torch.cat([ids, next_id.unsqueeze(0)], dim=1)
    print(f"  step {step:2d}: appended {tokenizer.decode([next_id.item()])!r}")
print(f"\nFull output: {tokenizer.decode(ids[0])!r}")

# Summary
# TODO: 3-5 lines. What did you learn about how generation actually works?
# the model is trained on a vast data first and then we send some input prompt and then it is
#  first tokenised goes through multiple layers of attention and feedforward network and the
# embeddings are modified understanding the context and then it goes through softmax where it gets
#  the probabilities of the next token and outputs whatever is the highest or near high we can set
#  the tempearature to near 0 to give higher chances to the ones with high probability or increase
#  temp to 2 (thats the max model allows) to give chances to other words whose probability
# is lower.
