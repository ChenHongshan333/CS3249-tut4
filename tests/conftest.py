import pytest


@pytest.fixture(autouse=True)
def no_real_llm(monkeypatch):
    """Tests never call a real LLM, even if your .env has an API key."""
    monkeypatch.setenv("LLM_PROVIDER", "none")
