"""Day 5: when should you use an LLM vs. a classical/local model for
classification?

Compares three approaches on the same small task:
  1. Zero-shot LLM prompting (via Gemini, using your existing llmkit)
  2. Local zero-shot classification (BART-MNLI, no training data needed)
  3. A simple classical baseline (TF-IDF + logistic regression) trained on
     a handful of labeled examples

Measures: accuracy, latency, and (for the LLM) cost.
"""
import time

# ---------------------------------------------------------------------------
# Test data: pretend support tickets + their true category
# ---------------------------------------------------------------------------
tickets = [
    ("I was charged twice for my subscription this month", "billing"),
    ("The app crashes every time I try to upload a photo", "technical"),
    ("I can't log into my account, it says invalid password", "account"),
    ("Can I get a refund for last month's charge?", "billing"),
    ("The website is really slow when I search for products", "technical"),
    ("I forgot my password and the reset email never arrived", "account"),
    ("Do you have a loyalty program or discounts for students?", "other"),
    ("My invoice shows an extra fee I don't recognize", "billing"),
    ("The mobile app keeps crashing on the checkout page", "technical"),
    ("I want to change the email linked to my account", "account"),
]
labels = ["billing", "technical", "account", "other"]

texts = [t for t, _ in tickets]
true_labels = [l for _, l in tickets]


# ---------------------------------------------------------------------------
# Approach 1: Local zero-shot model (BART-MNLI) — no training data needed
# ---------------------------------------------------------------------------
print("=== Approach 1: Local zero-shot (BART-MNLI) ===")
from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

zs_predictions = []
start = time.perf_counter()
for text in texts:
    result = classifier(text, candidate_labels=labels)
    pred = result["labels"][0]  # highest-scoring label
    zs_predictions.append(pred)
zs_latency = (time.perf_counter() - start) / len(texts) * 1000  # ms per item

zs_correct = sum(p == t for p, t in zip(zs_predictions, true_labels, strict=True))
print(f"Accuracy: {zs_correct}/{len(texts)}")
print(f"Avg latency per item: {zs_latency:.0f} ms")
for text, pred, true in zip(texts, zs_predictions, true_labels, strict=True):
    mark = "✓" if pred == true else "✗"
    print(f"  {mark} pred={pred:10s} true={true:10s} {text[:50]}")


# ---------------------------------------------------------------------------
# Approach 2: Classical baseline — TF-IDF + Logistic Regression
# Trained on a SEPARATE small labeled set, tested on the same `texts` above.
# ---------------------------------------------------------------------------
print("\n=== Approach 2: Classical (TF-IDF + Logistic Regression) ===")
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# A tiny "training set" — different examples than the test set above
train_texts = [
    "I need help with my bill this month",
    "There's an error on my invoice",
    "Please refund my last payment",
    "The app is not loading properly",
    "I'm getting an error message on checkout",
    "The website keeps freezing",
    "I can't access my account anymore",
    "Please reset my login credentials",
    "How do I update my email address",
    "What are your business hours",
    "Do you ship internationally",
    "Tell me about your company",
]
train_labels = [
    "billing", "billing", "billing",
    "technical", "technical", "technical",
    "account", "account", "account",
    "other", "other", "other",
]

vectorizer = TfidfVectorizer()
X_train = vectorizer.fit_transform(train_texts)
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train, train_labels)

start = time.perf_counter()
X_test = vectorizer.transform(texts)
clf_predictions = clf.predict(X_test)
clf_latency = (time.perf_counter() - start) / len(texts) * 1000

clf_correct = sum(p == t for p, t in zip(clf_predictions, true_labels, strict=True))
print(f"Accuracy: {clf_correct}/{len(texts)}")
print(f"Avg latency per item: {clf_latency:.2f} ms  <-- notice the scale vs above")
for text, pred, true in zip(texts, clf_predictions, true_labels, strict=True):
    mark = "✓" if pred == true else "✗"
    print(f"  {mark} pred={pred:10s} true={true:10s} {text[:50]}")


# ---------------------------------------------------------------------------
# Approach 3: LLM zero-shot prompting (Gemini via your llmkit)
# ---------------------------------------------------------------------------
print("\n=== Approach 3: LLM zero-shot (Gemini) ===")
import logging

from openai import OpenAI

from llmkit import estimate_cost, get_settings, setup_logging

setup_logging()
logging.getLogger("httpx").setLevel(logging.WARNING)
settings = get_settings()
client = OpenAI(
    api_key=settings.gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    # api_key=settings.groq_api_key,
    # base_url="https://api.groq.com/openai/v1",
)

# def classify_with_llm(text: str) -> tuple[str, int, int]:
#     prompt = (
#         f"Classify this support ticket into exactly one category: "
#         f"billing, technical, account, or other.\n\n"
#         f"Ticket: {text}\n\n"
#         f"Respond with ONLY the category name, nothing else."
#     )
#     resp = client.chat.completions.create(
#         model=settings.default_model,
#         messages=[{"role": "user", "content": prompt}],
#         max_tokens=1024,
#         temperature=0,
#     )
#     label = resp.choices[0].message.content.strip().lower()
#     return label, resp.usage.prompt_tokens, resp.usage.completion_tokens
gemini_client = OpenAI(
    api_key=settings.gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
groq_client = OpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)

def classify_with_llm(text: str) -> tuple[str, int, int]:
    prompt = (
        f"Classify this support ticket into exactly one category: "
        f"billing, technical, account, or other.\n\n"
        f"Ticket: {text}\n\n"
        f"Respond with ONLY the category name, nothing else."
    )

    # Try primary (Gemini) first, fall back to Groq on failure.
    try:
        resp = gemini_client.chat.completions.create(
            model=settings.default_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0,
        )
        model_used = settings.default_model
    except Exception as e:
        print(f"    [fallback] Gemini failed ({type(e).__name__}), trying Groq...")
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0,
        )
        model_used = "llama-3.3-70b-versatile"

    label = resp.choices[0].message.content.strip().lower()
    in_tok = resp.usage.prompt_tokens
    out_tok = resp.usage.completion_tokens
    print(f"    [debug] model={model_used} in_tok={resp.usage.prompt_tokens} "
      f"out_tok={resp.usage.completion_tokens}")
    return label, in_tok, out_tok, model_used  # note: now returns 4 values

llm_predictions = []
total_cost = 0.0
start = time.perf_counter()
for text in texts:
    pred, in_tok, out_tok, model_used = classify_with_llm(text)
    llm_predictions.append(pred)
    total_cost += estimate_cost(model_used, in_tok, out_tok)
llm_latency = (time.perf_counter() - start) / len(texts) * 1000

llm_correct = sum(p == t for p, t in zip(llm_predictions, true_labels, strict=True))
print(f"Accuracy: {llm_correct}/{len(texts)}")
print(f"Avg latency per item: {llm_latency:.0f} ms")
print(f"Total cost for {len(texts)} items: ${total_cost:.6f}")
for text, pred, true in zip(texts, llm_predictions, true_labels, strict=True):
    mark = "✓" if pred == true else "✗"
    print(f"  {mark} pred={pred:10s} true={true:10s} {text[:50]}")


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------
print("\n=== Summary ===")
print(f"{'Approach':30s} {'Accuracy':>10s} {'Latency/item':>14s} {'Cost/1k items':>15s}")
print(f"{'Local zero-shot (BART)':30s} {zs_correct}/{len(texts):>7d} {zs_latency:>12.0f}ms {'$0 (local)':>15s}")
print(f"{'Classical (TF-IDF+LogReg)':30s} {clf_correct}/{len(texts):>7d} {clf_latency:>12.2f}ms {'$0 (local)':>15s}")
print(f"{'LLM zero-shot (Gemini)':30s} {llm_correct}/{len(texts):>7d} {llm_latency:>12.0f}ms {f'${total_cost*100:.4f}':>15s}")

# # TODO: 4-5 lines — which approach would YOU pick for a real ticket-triage
# # system processing 50,000 tickets/month? Justify with the numbers above.