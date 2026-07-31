"""Day 1 test: proves your test setup works AND locks in cost math.

Cost accounting bugs are silent and expensive — this is a real production test,
not a toy. Run: pytest -q
"""

from llmkit import estimate_cost


def test_known_model_cost():
    # 1M input + 1M output tokens on haiku pricing (1.00 / 5.00 per MTok)
    assert estimate_cost("claude-haiku-4-5-20251001", 1_000_000, 1_000_000) == 6.00


def test_typical_request_cost():
    # 2k in, 500 out — a typical chat turn; should be fractions of a cent
    c = estimate_cost("claude-haiku-4-5-20251001", 2_000, 500)
    assert 0 < c < 0.01


def test_unknown_model_is_zero_not_crash():
    assert estimate_cost("mystery-model", 1000, 1000) == 0.0


def test_gemini_flash_cost():
    # 1M in + 1M out at Gemini Flash pricing (0.30 / 2.50 per MTok)
    assert estimate_cost("gemini-3.5-flash", 1_000_000, 1_000_000) == 2.80


def test_all_models_in_price_table_have_reasonable_prices():
    """Guards against typos like (999, 999) sneaking into the price table."""
    from llmkit.client import PRICES_PER_MTOK

    for model, (inp, outp) in PRICES_PER_MTOK.items():
        assert 0 < inp < 100, f"{model}: input price {inp} looks wrong"
        assert 0 < outp < 200, f"{model}: output price {outp} looks wrong"
