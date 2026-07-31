"""Ask Gemini which models this account can actually use.

The 404 tells us to 'Call ModelService.ListModels' — so we do exactly that.
Rule: when a provider gives you a discovery endpoint, trust it over any docs
or tutorial (including this one). Model availability varies by account age,
region, and rollout state.
"""

import httpx

from llmkit import get_settings

settings = get_settings()
url = "https://generativelanguage.googleapis.com/v1beta/models"
resp = httpx.get(url, params={"key": settings.gemini_api_key}, timeout=30)
resp.raise_for_status()
data = resp.json()

print(f"\nFound {len(data.get('models', []))} models available to your account:\n")
for m in data.get("models", []):
    name = m["name"].replace("models/", "")
    methods = m.get("supportedGenerationMethods", [])
    if "generateContent" in methods:
        print(f"  {name}")

print("\nPick one whose name contains 'flash' (not 'flash-live', not 'embedding').")
