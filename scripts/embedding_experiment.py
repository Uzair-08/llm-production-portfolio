"""Day 4: turn text into vectors, then measure similarity.

The foundation of RAG, semantic search, clustering, and deduplication.
No LLM in this script — just embeddings + math.
"""
import numpy as np
from sentence_transformers import SentenceTransformer

# 384-dim, ~25MB, CPU-fast. Runs on your laptop.
print("Loading all-MiniLM-L6-v2 (first run downloads ~25MB)...")
#model = SentenceTransformer("all-MiniLM-L6-v2")
model = SentenceTransformer("all-mpnet-base-v2")  # 768-dim, stronger model

def embed(texts: list[str]) -> np.ndarray:
    """Return an (N, 384) array of embeddings. Normalized to unit length so
    cosine similarity == dot product (faster + numerically stable)."""
    return model.encode(texts, normalize_embeddings=True)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors. Range: -1 to 1, higher = more similar.
    Since embeddings are normalized, this reduces to a simple dot product."""
    return float(np.dot(a, b))


# Experiment 1: pairwise similarity of a few sentences
print("\n=== Experiment 1: which pairs are most/least similar? ===")
texts = [
    "I love pizza",
    "Pizza is delicious",
    "I hate broccoli",
    "The Roman Empire fell in 476 AD",
    "Pizza was invented in Italy",
    "I love programming",
]
vecs = embed(texts)
# Print similarity matrix
print(f"{'':40s} " + " ".join(f"{i:>5d}" for i in range(len(texts))))
for i, t in enumerate(texts):
    row = " ".join(f"{cosine_sim(vecs[i], vecs[j]):>+5.2f}" for j in range(len(texts)))
    print(f"{i}: {t[:38]:40s} {row}")
# TODO: was your prediction correct? Which pairs surprised you?

# Experiment 2: semantic vs. lexical
print("\n=== Experiment 2: semantic search finds meaning, not keywords ===")
query = "how do I get a refund"
docs = [
    "Our return policy allows customers to send items back within 30 days.",
    "Refunds are processed within 5 business days after we receive the item.",
    "The company was founded in 2015 and is headquartered in Berlin.",
    "To reset your password, click 'Forgot password' on the login page.",
    "Money-back guarantees only apply to unused products in original packaging.",
]
q_vec = embed([query])[0]
d_vecs = embed(docs)
scores = [(cosine_sim(q_vec, d_vec), doc) for d_vec, doc in zip(d_vecs, docs, strict=True)]
scores.sort(reverse=True)
print(f"Query: {query!r}\nRanked docs:")
for score, doc in scores:
    print(f"  {score:+.3f}  {doc}")
# TODO: how many docs contained the literal word "refund"?
# How many were ranked in the top 2? What does this show?

# Experiment 3: exact-match failure — where embeddings LOSE
print("\n=== Experiment 3: where semantic search FAILS ===")
query = "error code E-4012"
docs = [
    "If you see error code E-4012, restart the router and try again.",
    "Common troubleshooting steps for connectivity issues include restarting.",
    "Our support team can be reached at support@example.com.",
    "The system logs all error codes for debugging purposes.",
    "Contact your ISP if the problem persists.",
    "banana is a fruit, not an error code. banana is a yellow fruit. and it is sold in dozens like 6 bananas or 12 bananas and minions like bananas",
    "i love mangoes",
]
q_vec = embed([query])[0]
d_vecs = embed(docs)
scores = [(cosine_sim(q_vec, d_vec), doc) for d_vec, doc in zip(d_vecs, docs, strict=True)]
scores.sort(reverse=True)
print(f"Query: {query!r}\nRanked docs:")
for score, doc in scores:
    print(f"  {score:+.3f}  {doc}")
# TODO: did the doc with the EXACT error code rank #1?
# What does the score gap between #1 and #2 look like?
# Why is this a production problem?
print("\n=== Experiment 3b: does query framing change the ranking? ===")
for query in ["error code E-4012", "E-4012", "problem with router E-4012 restart"]:
    q_vec = embed([query])[0]
    d_vecs = embed(docs)  # same docs as before
    scores = [(cosine_sim(q_vec, d_vec), doc) for d_vec, doc in zip(d_vecs, docs, strict=True)]
    scores.sort(reverse=True)
    print(f"\nQuery: {query!r}")
    for score, doc in scores[:3]:
        print(f"  {score:+.3f}  {doc[:60]}")
# Experiment 4: your own — pick two of these, or invent one
print("\n=== Experiment 4: your own ===")
# TODO: try one of:
#   (a) Paraphrase test: 3 versions of the same idea + 2 unrelated. Do the
#       paraphrases cluster?
#   (b) Multilingual: same sentence in English + Hindi + Telugu. Do they
#       land near each other? (This model is English-only, so this MAY fail —
#       which teaches you about model selection.)
#   (c) Negation: "I love pizza" vs "I do not love pizza". Are they similar
#       or opposite? Guess first, then check.


texts = [
    "I love burgers", 
    "I really enjoy eating pizza",
    "I ate biryani for lunch",
    "I have to go to school",
    "I am learning how to use embeddings",
]
for i in texts:
    for j in texts:
        print(cosine_sim(embed([i])[0], embed([j])[0]),end="   ")
    print()





# Summary
# TODO: 3-5 lines. What did you learn about how embeddings represent meaning?
# What did they get right? Where did they fail? Where would you use them
# in production, and where would you NOT?