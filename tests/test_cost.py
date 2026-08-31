"""Day 1 test: proves your test setup works AND locks in cost math.

Cost accounting bugs are silent and expensive — this is a real production test,
not a toy. Run: pytest -q
"""

from llmkit import estimate_cost


def test_unknown_model_is_zero_not_crash():
    assert estimate_cost("mystery-model", 1000, 1000) == 0.0


def test_gemini_flash_cost():
    # 1M in + 1M out at Gemini Flash pricing (0.30 / 2.50 per MTok)
    assert estimate_cost("gemini-3.5-flash", 1_000_000, 1_000_000) == 10.50


def test_all_models_in_price_table_have_reasonable_prices():
    """Guards against typos like (999, 999) sneaking into the price table."""
    from llmkit.client import PRICES_PER_MTOK

    for model, (inp, outp) in PRICES_PER_MTOK.items():
        assert 0 < inp < 100, f"{model}: input price {inp} looks wrong"
        assert 0 < outp < 200, f"{model}: output price {outp} looks wrong"
