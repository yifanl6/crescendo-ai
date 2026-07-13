import pytest


class FakeLLMClient:
    """Duck-types LLMClient with a scripted queue of responses, no network calls."""

    def __init__(self, json_responses=None, text_responses=None):
        self._json_responses = list(json_responses or [])
        self._text_responses = list(text_responses or [])
        self.json_calls = []
        self.text_calls = []

    def complete_json(self, system, user):
        self.json_calls.append((system, user))
        if not self._json_responses:
            return {}
        return self._json_responses.pop(0)

    def complete_text(self, system, user):
        self.text_calls.append((system, user))
        if not self._text_responses:
            return ""
        return self._text_responses.pop(0)


@pytest.fixture
def fake_llm():
    return FakeLLMClient()
