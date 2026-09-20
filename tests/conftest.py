"""Test-suite guards.

Iron rule from PROJECT.md: no live network in the suite. `config/providers.yaml` ships with the
real BORIS-NI WFS enabled, so anything calling `configured_providers()` would reach out. This
autouse fixture pins the provider config to "nothing configured" for every test; tests that want
providers build them explicitly (`StaticBodenrichtwert(...)`) or pass their own config dict.
"""

import pytest

from estatescout.scout import enrich as enrich_module

_NO_PROVIDERS = {
    "bodenrichtwert": {"provider": "none"},
    "region_signal": {"provider": "none"},
}


@pytest.fixture(autouse=True)
def no_live_providers(monkeypatch, request):
    if "live" in request.keywords:
        return  # opt-in live tests may use the real config
    monkeypatch.setattr(enrich_module, "load_provider_config", lambda path=None: _NO_PROVIDERS)
