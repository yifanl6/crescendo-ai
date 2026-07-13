from crescendo_ai.agents.music_advisor import MusicAdvisorAgent
from tests.conftest import FakeLLMClient


class FakeSearchClient:
    def __init__(self, results=None, error=None):
        self._results = results or []
        self._error = error

    def search(self, query, max_results=5):
        if self._error:
            raise self._error
        return self._results


def test_get_recommendations_summarizes_search_results():
    llm = FakeLLMClient(
        json_responses=[{"items": [{"headline": "Grant deadline", "detail": "Apply by August 1"}]}]
    )
    search = FakeSearchClient(
        results=[{"title": "Grant", "url": "http://x", "snippet": "Apply by August 1"}]
    )
    advisor = MusicAdvisorAgent(llm, search)

    recs = advisor.get_recommendations("music grants")

    assert recs["items"][0]["headline"] == "Grant deadline"
    assert recs["errors"] == []


def test_get_recommendations_handles_search_failure_gracefully():
    llm = FakeLLMClient()
    search = FakeSearchClient(error=RuntimeError("no api key"))
    advisor = MusicAdvisorAgent(llm, search)

    recs = advisor.get_recommendations("music grants")

    assert recs["items"] == []
    assert recs["errors"]
