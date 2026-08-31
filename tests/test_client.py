from llmkit.client import PROVIDER_BASE_URLS, estimate_cost


def test_estimate_cost_known_model():
    assert estimate_cost("llama-3.3-70b-versatile", 1_000_000, 1_000_000) == 1.38


def test_every_priced_model_has_a_base_url():
    """Every model we can price should also be callable — catches config drift."""
    from llmkit.client import PRICES_PER_MTOK
    for model in PRICES_PER_MTOK:
        assert model in PROVIDER_BASE_URLS, f"{model} has a price but no base_url"